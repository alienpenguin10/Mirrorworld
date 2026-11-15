# Mirrorworld addition (not in upstream streetlevel).
"""
Entwine Point Tile (EPT) reader: https://entwine.io/en/latest/entwine-point-tile.html

An EPT dataset is an octree of LAZ files (``ept-data/D-X-Y-Z.laz``) with a JSON hierarchy of point counts.
Deeper levels add detail: the point spacing halves with each level.
"""
import asyncio
import math
from dataclasses import dataclass
from io import BytesIO
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
from aiohttp import ClientSession, ClientTimeout

from ..aerial.util import run_sync
from ..raster import bbox_to_crs

HEADERS = {"User-Agent": "mirrorworld (Python)"}


@dataclass
class EptInfo:
    """The header of an EPT dataset (``ept.json``)."""

    url: str
    """Base URL of the dataset (without ``/ept.json``)."""
    bounds: Tuple[float, float, float, float, float, float]
    """Octree cube: minx, miny, minz, maxx, maxy, maxz."""
    bounds_conforming: Tuple[float, float, float, float, float, float]
    """Tight bounds of the actual points."""
    span: int
    """Grid cells per node edge; the root node's point spacing is cube width / span."""
    points: int
    """Total number of points."""
    crs: Optional[str]
    """Horizontal CRS, e.g. ``EPSG:3857``."""
    schema: List[dict]
    """Point dimensions with scale/offset."""

    def spacing(self, depth: int) -> float:
        """Approximate point spacing in CRS units at an octree depth."""
        return (self.bounds[3] - self.bounds[0]) / self.span / 2 ** depth

    def depth_for_resolution(self, resolution: float) -> int:
        """Shallowest depth whose point spacing is at most ``resolution``."""
        return max(0, math.ceil(math.log2((self.bounds[3] - self.bounds[0]) / self.span / resolution)))


def require_laspy():
    try:
        import laspy
        return laspy
    except ImportError as e:
        raise ImportError("This function needs laspy with LAZ support: pip install mirrorworld[lidar]") from e


def get_info(url: str) -> EptInfo:
    """
    Reads the header of an EPT dataset.

    :param url: Dataset URL, with or without ``/ept.json``.
    :return: An EptInfo.
    """
    return run_sync(get_info_async, url)


async def get_info_async(url: str, session: ClientSession) -> EptInfo:
    base = url[:-len("/ept.json")] if url.endswith("/ept.json") else url.rstrip("/")
    async with session.get(f"{base}/ept.json", headers=HEADERS) as response:
        response.raise_for_status()
        data = await response.json(content_type=None)
    srs = data.get("srs") or {}
    crs = f"{srs['authority']}:{srs['horizontal']}" if srs.get("authority") and srs.get("horizontal") else srs.get("wkt")
    return EptInfo(url=base, bounds=tuple(data["bounds"]), bounds_conforming=tuple(data.get("boundsConforming",
                   data["bounds"])), span=data["span"], points=data["points"], crs=crs, schema=data["schema"])


def get_points(url: str, north: float, west: float, south: float, east: float, resolution: Optional[float] = None,
               classes: Optional[Iterable[int]] = None, max_points: int = 50_000_000,
               max_concurrency: int = 8):
    """
    Reads the points of an EPT dataset inside a bounding box.

    :param url: Dataset URL.
    :param north: Latitude of the top edge.
    :param west: Longitude of the left edge.
    :param south: Latitude of the bottom edge.
    :param east: Longitude of the right edge.
    :param resolution: *(optional)* Wanted point spacing in CRS units; deeper (denser) octree levels are skipped.
        Defaults to all points.
    :param classes: *(optional)* Keep only these ASPRS classification codes, e.g. ``[2]`` (ground) or
        ``[6]`` (building). Defaults to all.
    :param max_points: *(optional)* Refuse requests whose candidate nodes hold more points than this.
        Defaults to 50 million.
    :param max_concurrency: *(optional)* Maximum number of simultaneous downloads. Defaults to 8.
    :return: A ``laspy.LasData`` in the dataset's CRS (written into the header).
    """
    return run_sync(get_points_async, url, north, west, south, east, resolution=resolution, classes=classes,
                    max_points=max_points, max_concurrency=max_concurrency)


async def get_points_async(url: str, north: float, west: float, south: float, east: float, session: ClientSession,
                           resolution: Optional[float] = None, classes: Optional[Iterable[int]] = None,
                           max_points: int = 50_000_000, max_concurrency: int = 8):
    laspy = require_laspy()
    info = await get_info_async(url, session)
    minx, miny, maxx, maxy = bbox_to_crs(north, west, south, east, info.crs)
    max_depth = info.depth_for_resolution(resolution) if resolution else None
    nodes = await select_nodes_async(info, (minx, miny, maxx, maxy), max_depth, session)
    total = sum(count for _, count in nodes)
    if total > max_points:
        raise ValueError(f"The selected octree nodes hold {total:,} points (> max_points={max_points:,}); "
                         f"pass a coarser resolution or a smaller box")

    semaphore = asyncio.Semaphore(max_concurrency)

    async def fetch(key):
        async with semaphore:
            for attempt in range(4):
                try:
                    async with session.get(f"{info.url}/ept-data/{key}.laz", headers=HEADERS,
                                           timeout=ClientTimeout(total=300)) as response:
                        response.raise_for_status()
                        return await response.read()
                except Exception:
                    if attempt == 3:
                        raise
                    await asyncio.sleep(2 ** attempt)

    blobs = await asyncio.gather(*(fetch(key) for key, _ in nodes))
    return merge_nodes(laspy, blobs, (minx, miny, maxx, maxy), info.crs, classes)


def download_points(url: str, north: float, west: float, south: float, east: float, path: str, **kwargs):
    """
    Same as :func:`get_points`, then writes a ``.laz`` or ``.las`` file.

    :param path: Output path.
    :return: The ``laspy.LasData``.
    """
    las = get_points(url, north, west, south, east, **kwargs)
    las.write(path)
    return las


async def select_nodes_async(info: EptInfo, bbox: Tuple[float, float, float, float], max_depth: Optional[int],
                             session: ClientSession) -> List[Tuple[str, int]]:
    """Walks the hierarchy and returns (node key, point count) for nodes that intersect the box."""
    selected = []

    async def load(key: str) -> Dict[str, int]:
        async with session.get(f"{info.url}/ept-hierarchy/{key}.json", headers=HEADERS) as response:
            response.raise_for_status()
            return await response.json(content_type=None)

    pending = ["0-0-0-0"]
    while pending:
        hierarchies = await asyncio.gather(*(load(k) for k in pending))
        pending = []
        for hierarchy in hierarchies:
            for key, count in hierarchy.items():
                depth = int(key.split("-")[0])
                if max_depth is not None and depth > max_depth:
                    continue
                if not node_intersects(info.bounds, key, bbox):
                    continue
                if count == -1:
                    # The subtree rooted here is described in its own file.
                    if key not in pending:
                        pending.append(key)
                elif count > 0:
                    selected.append((key, count))
    return selected


def node_bounds(cube: Tuple[float, ...], key: str) -> Tuple[float, float, float, float]:
    """Horizontal bounds (minx, miny, maxx, maxy) of the octree node ``D-X-Y-Z``."""
    depth, x, y, _ = (int(v) for v in key.split("-"))
    size_x = (cube[3] - cube[0]) / 2 ** depth
    size_y = (cube[4] - cube[1]) / 2 ** depth
    minx, miny = cube[0] + x * size_x, cube[1] + y * size_y
    return minx, miny, minx + size_x, miny + size_y


def node_intersects(cube, key: str, bbox) -> bool:
    nx0, ny0, nx1, ny1 = node_bounds(cube, key)
    bx0, by0, bx1, by1 = bbox
    return nx0 <= bx1 and nx1 >= bx0 and ny0 <= by1 and ny1 >= by0


def merge_nodes(laspy, blobs: List[bytes], bbox, crs: Optional[str], classes: Optional[Iterable[int]]):
    """Decodes LAZ nodes, crops them to the box and merges them into one LasData."""
    minx, miny, maxx, maxy = bbox
    classes = set(classes) if classes is not None else None
    out, records = None, []
    for blob in blobs:
        las = laspy.read(BytesIO(blob))
        mask = (las.x >= minx) & (las.x <= maxx) & (las.y >= miny) & (las.y <= maxy)
        if classes is not None:
            mask &= np.isin(np.asarray(las.classification), list(classes))
        if out is None:
            header = laspy.LasHeader(point_format=las.header.point_format, version=las.header.version)
            header.scales, header.offsets = las.header.scales, las.header.offsets
            out = laspy.LasData(header)
        points = las.points[mask]
        if not np.allclose(las.header.scales, out.header.scales) or not np.allclose(las.header.offsets,
                                                                                    out.header.offsets):
            # Re-quantize to the first node's scale/offset.
            array = points.array.copy()
            for dim, i in (("X", 0), ("Y", 1), ("Z", 2)):
                real = array[dim] * las.header.scales[i] + las.header.offsets[i]
                array[dim] = np.round((real - out.header.offsets[i]) / out.header.scales[i]).astype(array[dim].dtype)
            points = laspy.PackedPointRecord(array, out.header.point_format)
        records.append(points.array)
    if out is None:
        raise ValueError("No points in the box")
    out.points = laspy.ScaleAwarePointRecord(np.concatenate(records), out.header.point_format,
                                             out.header.scales, out.header.offsets)
    out.update_header()
    if crs and crs.startswith("EPSG:"):
        try:
            from pyproj import CRS
            out.header.add_crs(CRS.from_user_input(crs))
        except Exception:
            pass
    return out
