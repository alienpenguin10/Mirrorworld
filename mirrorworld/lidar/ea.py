# Mirrorworld addition (not in upstream streetlevel).
"""
Environment Agency LiDAR point clouds for England, from the Defra Survey Data Download service
(https://environment.data.gov.uk/survey). Open Government Licence v3 (attribution: Environment Agency), no key.

The default product is the National LIDAR Programme (NLP) point cloud, surveyed since 2016/17. The data comes as
whole 5 km British National Grid tiles (e.g. ``TL4055``), one zipped LAZ per tile and survey year, typically
0.2-0.4 GB each: there is no way to fetch only part of a tile. Tiles are downloaded once into a cache directory
and cropped locally.

Points are in EPSG:27700 with heights in meters above Ordnance Datum Newlyn, classified to ASPRS codes
(1 unclassified, 2 ground, 3-5 vegetation, 6 building, 7 noise), without RGB. Surveys up to 2021 are mostly
LAS 1.2 point format 1, later ones LAS 1.4 point format 6; density is about 2-6 points per m², higher in recent
years. The year is the survey's nominal year; the file name records the flight dates, which can start in the
previous winter.

:func:`search` asks the service which tiles, products and years cover a box (the same request as the download
page's "Get available tiles"). Don't guess years by requesting tile URLs: under load the service answers
"no data" for tiles that exist.
"""
import glob
import json
import os
import re
import time
import zipfile
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import requests

from .ept import HEADERS, require_laspy
from ..raster import bbox_to_crs

SEARCH_URL = "https://environment.data.gov.uk/tiles/collections/survey/search"
PRODUCT = "national_lidar_programme_point_cloud"
TILE_SIZE = 5000
CRS = "EPSG:27700"
_LETTERS = "ABCDEFGHJKLMNOPQRSTUVWXYZ"   # OS grid letters: no I


@dataclass
class Tile:
    """One downloadable tile of one survey product and year."""

    product: str
    """Product ID, e.g. ``national_lidar_programme_point_cloud`` or ``national_lidar_programme_dtm``."""
    year: int
    """Survey year."""
    resolution: str
    """Resolution ID as the service gives it (``1`` for 1 m rasters and NLP point clouds; may be ``NaN``)."""
    tile: str
    """5 km tile name, e.g. ``TL4055``."""
    label: str
    """The service's label, e.g. ``national_lidar_programme_point_cloud-2023-1m-TL45ne``."""
    url: str
    """Download URL of the zip."""


def search(north: float, west: float, south: float, east: float, product: Optional[str] = PRODUCT) -> List[Tile]:
    """
    Lists the tiles covering a bounding box, from the service's own tile search.

    :param north: Latitude of the top edge.
    :param west: Longitude of the left edge.
    :param south: Latitude of the bottom edge.
    :param east: Longitude of the right edge.
    :param product: *(optional)* Keep only this product. Defaults to the NLP point cloud; ``None`` returns every
        survey product (DTM/DSM rasters, older ``lidar_point_cloud`` surveys, aerial photography, ...).
    :return: Tiles sorted by tile name, then newest year first.
    """
    ring = [[west, south], [east, south], [east, north], [west, north], [west, south]]
    response = _request("POST", SEARCH_URL, data=json.dumps({"type": "Polygon", "coordinates": [ring]}),
                        headers={**HEADERS, "Content-Type": "application/geo+json"})
    response.raise_for_status()
    tiles = []
    for result in response.json().get("results", []):
        if product is not None and result["product"]["id"] != product:
            continue
        tiles.append(Tile(product=result["product"]["id"], year=int(result["year"]["id"]),
                          resolution=str(result["resolution"]["id"]), tile=result["tile"]["id"],
                          label=result.get("label", ""), url=result["uri"]))
    return sorted(tiles, key=lambda t: (t.tile, t.product, -t.year))


def find_years(tile: str, product: str = PRODUCT) -> List[int]:
    """
    Lists the survey years available for a 5 km tile, newest first.

    :param tile: Tile name, e.g. ``TL4055``.
    :param product: *(optional)* Product ID. Defaults to the NLP point cloud.
    :return: Years with data (possibly empty).
    """
    return [t.year for t in _tile_entries(tile, product)]


def download_tile(tile: str, year: Optional[int] = None, directory: Optional[str] = None,
                  product: str = PRODUCT) -> str:
    """
    Downloads one tile and extracts its LAZ, unless it is already in ``directory``. The zip is not kept.

    :param tile: Tile name, e.g. ``TL4055``.
    :param year: *(optional)* Survey year. Defaults to the newest available.
    :param directory: *(optional)* Where to keep the LAZ files. Defaults to :func:`cache_dir`.
    :param product: *(optional)* Point cloud product ID. Defaults to the NLP point cloud.
    :return: Path of the LAZ file, ``<directory>/<product>/<year>/<name>.laz``, keeping the provider's file name
        (tile, survey project and flight dates, e.g. ``TL4055_P_12744_20230213_20230213.laz``).
    :raises ValueError: If the tile has no data (for that year), or the zip does not hold exactly one LAZ.
    """
    tile = tile.upper()
    if year is not None:
        cached = _cached(tile, year, directory, product)
        if cached:
            return cached
    entries = _tile_entries(tile, product)
    if year is not None:
        entries = [e for e in entries if e.year == year]
    if not entries:
        raise ValueError(f"No {product} data for tile {tile}" + (f" in {year}" if year else ""))
    return _download(entries[0], directory)


def get_points(north: float, west: float, south: float, east: float, year: Optional[int] = None,
               directory: Optional[str] = None, classes: Optional[Iterable[int]] = None, max_tiles: int = 4,
               product: str = PRODUCT):
    """
    Reads point cloud data inside a bounding box, downloading the 5 km tiles it touches if they are not cached.

    :param north: Latitude of the top edge.
    :param west: Longitude of the left edge.
    :param south: Latitude of the bottom edge.
    :param east: Longitude of the right edge.
    :param year: *(optional)* Survey year for every tile. Defaults to the newest year of each tile, so a box across
        a tile edge can mix survey years.
    :param directory: *(optional)* Where to keep the downloaded tiles. Defaults to :func:`cache_dir`.
    :param classes: *(optional)* Keep only these ASPRS classes, e.g. ``[2]`` for ground.
    :param max_tiles: *(optional)* Refuse boxes needing more tiles than this (each is a 0.2-0.4 GB download).
        Defaults to 4.
    :param product: *(optional)* Point cloud product ID. Defaults to the NLP point cloud.
    :return: A ``laspy.LasData`` in EPSG:27700, heights above Ordnance Datum Newlyn.
    :raises ValueError: If the box needs too many tiles, or no tile has data.
    """
    by_tile: Dict[str, Tile] = {}
    for entry in search(north, west, south, east, product):
        if (year is None or entry.year == year) and entry.tile not in by_tile:
            by_tile[entry.tile] = entry   # newest first, so the first entry per tile is the newest
    if not by_tile:
        raise ValueError(f"No {product} data in this box" + (f" for {year}" if year else ""))
    if len(by_tile) > max_tiles:
        raise ValueError(f"The box needs {len(by_tile)} tiles (> max_tiles={max_tiles}); each is a 0.2-0.4 GB "
                         f"download. Pass a smaller box or a larger max_tiles")
    paths = [_cached(t.tile, t.year, directory, product) or _download(t, directory) for t in by_tile.values()]
    return crop_files(paths, bbox_to_crs(north, west, south, east, CRS), classes)


def download_points(north: float, west: float, south: float, east: float, path: str, **kwargs):
    """
    Same as :func:`get_points`, then writes a ``.laz`` or ``.las`` file.

    :param path: Output path.
    :return: The ``laspy.LasData``.
    """
    las = get_points(north, west, south, east, **kwargs)
    las.write(path)
    return las


def crop_files(paths: List[str], bounds: Tuple[float, float, float, float],
               classes: Optional[Iterable[int]] = None, chunk_size: int = 5_000_000):
    """
    Crops LAS/LAZ files to a box and merges them, reading in chunks so whole tiles never sit in memory.

    :param paths: LAS/LAZ files in one CRS.
    :param bounds: minx, miny, maxx, maxy in the files' CRS.
    :param classes: *(optional)* Keep only these ASPRS classes.
    :param chunk_size: *(optional)* Points read at a time.
    :return: A ``laspy.LasData`` with the header (point format, scales, offsets, CRS) of the first file with points
        in the box; points from files in another point format are converted to it.
    """
    laspy = require_laspy()
    minx, miny, maxx, maxy = bounds
    classes = list(classes) if classes is not None else None
    out, records = None, []
    for path in paths:
        with laspy.open(path) as reader:
            for chunk in reader.chunk_iterator(chunk_size):
                # chunk.x/.y are already scaled float64; float32 would lose centimeters at BNG magnitudes.
                mask = (chunk.x >= minx) & (chunk.x <= maxx) & (chunk.y >= miny) & (chunk.y <= maxy)
                if classes is not None:
                    mask &= np.isin(np.asarray(chunk.classification), classes)
                if not mask.any():
                    continue
                if out is None:
                    out = laspy.LasData(reader.header)
                array = chunk.array[mask]
                if reader.header.point_format.id != out.header.point_format.id:
                    part = laspy.LasData(reader.header)
                    part.points = laspy.ScaleAwarePointRecord(array, reader.header.point_format,
                                                              reader.header.scales, reader.header.offsets)
                    array = laspy.convert(part, point_format_id=out.header.point_format.id,
                                          file_version=str(out.header.version)).points.array
                if not (np.allclose(reader.header.scales, out.header.scales)
                        and np.allclose(reader.header.offsets, out.header.offsets)):
                    array = array.copy()
                    for dim, i in (("X", 0), ("Y", 1), ("Z", 2)):
                        real = array[dim] * reader.header.scales[i] + reader.header.offsets[i]
                        array[dim] = np.round((real - out.header.offsets[i]) / out.header.scales[i])
                records.append(array)
    if not records:
        raise ValueError("No points in the box")
    out.points = laspy.ScaleAwarePointRecord(np.concatenate(records), out.header.point_format,
                                             out.header.scales, out.header.offsets)
    out.update_header()
    return out


def tile_name(easting: float, northing: float) -> str:
    """
    Name of the 5 km tile containing a British National Grid point, e.g. ``TL4055`` for E 541000, N 257500.

    :param easting: Easting in meters (EPSG:27700).
    :param northing: Northing in meters.
    :return: Two grid letters, then the easting and northing km of the tile's south-west corner (two digits each).
    """
    e, n = int(easting // 1000), int(northing // 1000)
    if not (0 <= e < 700 and 0 <= n < 1300):
        raise ValueError(f"({easting}, {northing}) is outside the British National Grid")
    e100, n100 = e // 100, n // 100
    first = _LETTERS[(19 - n100) - (19 - n100) % 5 + (e100 + 10) // 5]
    second = _LETTERS[(19 - n100) * 5 % 25 + e100 % 5]
    return f"{first}{second}{e % 100 // 5 * 5:02d}{n % 100 // 5 * 5:02d}"


def tile_bounds(tile: str) -> Tuple[float, float, float, float]:
    """
    Bounds of a 5 km tile in EPSG:27700.

    :param tile: Tile name, e.g. ``TL4055``.
    :return: minx, miny, maxx, maxy in meters.
    """
    tile = tile.upper()
    i, j = _LETTERS.index(tile[0]), _LETTERS.index(tile[1])
    e = ((i % 5) * 5 + j % 5 - 10) * 100_000 + int(tile[2:4]) * 1000
    n = (19 - (i // 5) * 5 - j // 5) * 100_000 + int(tile[4:6]) * 1000
    return float(e), float(n), float(e + TILE_SIZE), float(n + TILE_SIZE)


def cache_dir() -> str:
    """
    Default tile cache: ``$MIRRORWORLD_CACHE/ea-lidar`` if set, else ``$XDG_CACHE_HOME/mirrorworld/ea-lidar``,
    else ``~/.cache/mirrorworld/ea-lidar``.
    """
    if os.environ.get("MIRRORWORLD_CACHE"):
        return os.path.join(os.environ["MIRRORWORLD_CACHE"], "ea-lidar")
    base = os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache")
    return os.path.join(base, "mirrorworld", "ea-lidar")


def _tile_entries(tile: str, product: str) -> List[Tile]:
    """Search entries for one tile, newest first; the search box is the tile shrunk by 50 m, in WGS84."""
    from pyproj import Transformer
    tile = tile.upper()
    minx, miny, maxx, maxy = tile_bounds(tile)
    to_wgs84 = Transformer.from_crs(CRS, "EPSG:4326", always_xy=True)
    lons, lats = to_wgs84.transform([minx + 50, maxx - 50, maxx - 50, minx + 50],
                                    [miny + 50, miny + 50, maxy - 50, maxy - 50])
    return [t for t in search(max(lats), min(lons), min(lats), max(lons), product) if t.tile == tile]


def _folder(year: int, directory: Optional[str], product: str) -> str:
    return os.path.join(directory or cache_dir(), product, str(year))


def _cached(tile: str, year: int, directory: Optional[str], product: str) -> Optional[str]:
    found = sorted(glob.glob(os.path.join(glob.escape(_folder(year, directory, product)), f"{tile}*.laz")))
    return found[0] if found else None


def _download(entry: Tile, directory: Optional[str]) -> str:
    folder = _folder(entry.year, directory, entry.product)
    os.makedirs(folder, exist_ok=True)
    part = os.path.join(folder, f"{entry.tile}.zip.part")
    path = os.path.join(folder, f"{entry.tile}.laz")
    try:
        # The service may take a couple of minutes to prepare a zip before sending it.
        with _request("GET", entry.url, stream=True, timeout=600) as response:
            chunks = response.iter_content(1 << 20)
            first = next(chunks, b"")
            if not _is_zip(first):
                raise ValueError(f"{entry.url} did not return a zip (HTTP {response.status_code}): {first[:100]!r}")
            with open(part, "wb") as f:
                f.write(first)
                for chunk in chunks:
                    f.write(chunk)
        with zipfile.ZipFile(part) as archive:
            members = [m for m in archive.infolist() if m.filename.lower().endswith(".laz")]
            if len(members) != 1:
                raise ValueError(f"Expected one LAZ in {entry.url}, found {[m.filename for m in archive.infolist()]}")
            # Keep the provider's name if it is a plain one for this tile; never let the archive choose a path.
            name = os.path.basename(members[0].filename.replace("\\", "/"))
            if re.fullmatch(rf"{entry.tile}[A-Za-z0-9_.-]*\.laz", name, flags=re.IGNORECASE):
                path = os.path.join(folder, name)
            with archive.open(members[0]) as src, open(path + ".part", "wb") as dst:
                while block := src.read(1 << 20):
                    dst.write(block)
        os.replace(path + ".part", path)
    finally:
        for leftover in (part, path + ".part"):
            if os.path.exists(leftover):
                os.remove(leftover)
    return path


def _is_zip(head: bytes) -> bool:
    # Decide by content, not status: "no data" is a small JSON body, and the status has been seen to disagree.
    return head[:2] == b"PK"


def _request(method: str, url: str, timeout: float = 120, attempts: int = 6, **kwargs) -> requests.Response:
    """Request that waits out rate limiting (429) and transient server errors."""
    kwargs.setdefault("headers", HEADERS)
    for attempt in range(attempts):
        response = requests.request(method, url, timeout=timeout, **kwargs)
        if response.status_code != 429 and response.status_code < 500:
            return response
        response.close()
        if attempt == attempts - 1:
            response.raise_for_status()
        retry_after = response.headers.get("Retry-After", "")
        time.sleep(float(retry_after) if retry_after.isdigit() else min(60, 5 * 2 ** attempt))
    raise AssertionError("unreachable")
