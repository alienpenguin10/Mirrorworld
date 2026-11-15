# Mirrorworld addition (not in upstream streetlevel).
"""
USGS 3D Elevation Program (3DEP) LiDAR point clouds, published as Entwine Point Tiles on AWS
(``s3://usgs-lidar-public``, https://registry.opendata.aws/usgs-lidar/). Public domain, no key.
Points come in Web Mercator (EPSG:3857) with heights in meters, classified to ASPRS codes
(2 ground, 3-5 vegetation, 6 building, 9 water, ...).
"""
import re
from dataclasses import dataclass
from typing import Iterable, List, Optional

import requests

from . import ept

BOUNDARIES_URL = "https://raw.githubusercontent.com/hobuinc/usgs-lidar/master/boundaries/resources.geojson"
_boundaries_cache: Optional[dict] = None


@dataclass
class Dataset:
    """One 3DEP LiDAR survey."""

    name: str
    """Survey name, e.g. ``WA_KingCo_1_2021``."""
    url: str
    """EPT dataset URL."""
    points: Optional[int]
    """Total number of points."""
    year: Optional[int]
    """Year parsed from the name, if any."""


def find_datasets(north: float, west: float, south: float, east: float, refresh: bool = False) -> List[Dataset]:
    """
    Lists the surveys whose coverage intersects a bounding box, newest first.

    :param north: Latitude of the top edge.
    :param west: Longitude of the left edge.
    :param south: Latitude of the bottom edge.
    :param east: Longitude of the right edge.
    :param refresh: *(optional)* Re-download the coverage index (~9 MB, cached for the session).
    :return: A list of Dataset objects.
    """
    global _boundaries_cache
    if _boundaries_cache is None or refresh:
        response = requests.get(BOUNDARIES_URL, headers=ept.HEADERS, timeout=120)
        response.raise_for_status()
        _boundaries_cache = response.json()
    found = []
    for feature in _boundaries_cache.get("features", []):
        if _intersects(feature.get("geometry"), north, west, south, east):
            props = feature.get("properties", {})
            name = props.get("name", "")
            years = [int(y) for y in re.findall(r"(?<!\d)(19\d\d|20\d\d)(?!\d)", name)]
            found.append(Dataset(name=name, url=props.get("url", "").replace("/ept.json", ""),
                                 points=props.get("count"), year=max(years) if years else None))
    return sorted(found, key=lambda d: d.year or 0, reverse=True)


def get_points(north: float, west: float, south: float, east: float, dataset: Optional[str] = None,
               resolution: Optional[float] = None, classes: Optional[Iterable[int]] = None,
               max_points: int = 50_000_000):
    """
    Reads 3DEP LiDAR points inside a bounding box.

    :param north: Latitude of the top edge.
    :param west: Longitude of the left edge.
    :param south: Latitude of the bottom edge.
    :param east: Longitude of the right edge.
    :param dataset: *(optional)* Survey name from :func:`find_datasets`. Defaults to the newest one covering the
        box.
    :param resolution: *(optional)* Wanted point spacing in meters (Web Mercator units). Defaults to all points.
    :param classes: *(optional)* Keep only these ASPRS classes, e.g. ``[6]`` for buildings.
    :param max_points: *(optional)* Refuse larger requests. Defaults to 50 million.
    :return: A ``laspy.LasData`` in EPSG:3857.
    """
    return ept.get_points(_dataset_url(north, west, south, east, dataset), north, west, south, east,
                          resolution=resolution, classes=classes, max_points=max_points)


async def get_points_async(north: float, west: float, south: float, east: float, session,
                           dataset: Optional[str] = None, resolution: Optional[float] = None,
                           classes: Optional[Iterable[int]] = None, max_points: int = 50_000_000):
    return await ept.get_points_async(_dataset_url(north, west, south, east, dataset), north, west, south, east,
                                      session, resolution=resolution, classes=classes, max_points=max_points)


def download_points(north: float, west: float, south: float, east: float, path: str, **kwargs):
    """
    Same as :func:`get_points`, then writes a ``.laz`` or ``.las`` file.

    :param path: Output path.
    :return: The ``laspy.LasData``.
    """
    las = get_points(north, west, south, east, **kwargs)
    las.write(path)
    return las


def _dataset_url(north, west, south, east, dataset) -> str:
    datasets = find_datasets(north, west, south, east)
    if dataset:
        for candidate in datasets:
            if candidate.name == dataset:
                return candidate.url
        return f"https://s3-us-west-2.amazonaws.com/usgs-lidar-public/{dataset}"
    if not datasets:
        raise ValueError("No 3DEP LiDAR dataset covers this box")
    return datasets[0].url


def _intersects(geometry, north, west, south, east) -> bool:
    if not geometry:
        return False
    polygons = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
    for polygon in polygons:
        ring = polygon[0]
        xs, ys = [p[0] for p in ring], [p[1] for p in ring]
        if max(xs) < west or min(xs) > east or max(ys) < south or min(ys) > north:
            continue
        corners = [(west, south), (west, north), (east, south), (east, north),
                   ((west + east) / 2, (south + north) / 2)]
        if any(_in_ring(x, y, ring) for x, y in corners):
            return True
        if any(west <= x <= east and south <= y <= north for x, y in ring):
            return True
    return False


def _in_ring(x, y, ring) -> bool:
    inside = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside
