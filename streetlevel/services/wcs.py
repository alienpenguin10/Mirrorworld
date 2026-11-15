# Mirrorworld addition (not in upstream streetlevel).
"""OGC Web Coverage Service (WCS 2.0.1) client, for gridded values such as elevation models. Needs rasterio."""
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Optional, Tuple

from aiohttp import ClientSession

from .util import fetch_bytes_async, raise_if_error_document, mosaic_async, make_raster, ServiceError
from ..aerial.util import run_sync
from ..raster import Raster, bbox_to_crs, grid_for_bounds, read_geotiff


@dataclass
class CoverageDescription:
    """The grid of a coverage."""

    coverage_id: str
    crs: str
    """Native CRS, e.g. ``EPSG:28992``."""
    axis_labels: List[str]
    """Axis names used in ``subset`` parameters, in CRS order, e.g. ``["x", "y"]``."""
    resolution: Tuple[float, float]
    """Native pixel size in CRS units."""
    bounds: Tuple[float, float, float, float]
    """minx, miny, maxx, maxy in the native CRS (x/y order)."""


def get_coverage_ids(url: str) -> List[str]:
    """
    Lists the coverages a WCS offers.

    :param url: Service URL.
    :return: Coverage IDs.
    """
    return run_sync(get_coverage_ids_async, url)


async def get_coverage_ids_async(url: str, session: ClientSession) -> List[str]:
    body, _ = await fetch_bytes_async(session, url, {"service": "WCS", "version": "2.0.1",
                                                     "request": "GetCapabilities"})
    return re.findall(r"<(?:\w+:)?CoverageId>([^<]+)</(?:\w+:)?CoverageId>", body.decode())


def describe_coverage(url: str, coverage_id: str) -> CoverageDescription:
    """
    Reads the native CRS, axes, resolution and extent of a coverage.

    :param url: Service URL.
    :param coverage_id: The coverage ID.
    :return: A CoverageDescription.
    """
    return run_sync(describe_coverage_async, url, coverage_id)


async def describe_coverage_async(url: str, coverage_id: str, session: ClientSession) -> CoverageDescription:
    body, _ = await fetch_bytes_async(session, url, {"service": "WCS", "version": "2.0.1",
                                                     "request": "DescribeCoverage", "coverageId": coverage_id})
    return parse_coverage_description(body, coverage_id)


def get_raster(url: str, coverage_id: str, north: float, west: float, south: float, east: float,
               max_size: int = 4000, max_concurrency: int = 4) -> Raster:
    """
    Downloads a coverage for a bounding box at its native resolution and CRS, in chunks for large areas.

    :param url: Service URL.
    :param coverage_id: The coverage ID.
    :param north: Latitude of the top edge.
    :param west: Longitude of the left edge.
    :param south: Latitude of the bottom edge.
    :param east: Longitude of the right edge.
    :param max_size: *(optional)* Largest chunk side in pixels. Defaults to 4000.
    :param max_concurrency: *(optional)* Maximum number of simultaneous requests. Defaults to 4.
    :return: The raster, with the service's data type and nodata value.
    :raises ValueError: If the box lies outside the coverage's extent.
    """
    return run_sync(get_raster_async, url, coverage_id, north, west, south, east, max_size=max_size,
                    max_concurrency=max_concurrency)


async def get_raster_async(url: str, coverage_id: str, north: float, west: float, south: float, east: float,
                           session: ClientSession, max_size: int = 4000, max_concurrency: int = 4) -> Raster:
    desc = await describe_coverage_async(url, coverage_id, session)
    res_x, res_y = desc.resolution
    minx, miny, maxx, maxy = bbox_to_crs(north, west, south, east, desc.crs)
    cx0, cy0, cx1, cy1 = desc.bounds
    if maxx <= cx0 or minx >= cx1 or maxy <= cy0 or miny >= cy1:
        raise ValueError(f"The bounding box is outside the extent of coverage {coverage_id} "
                         f"({cx0}, {cy0}, {cx1}, {cy1} in {desc.crs})")
    # Snap to the coverage's own grid so pixels are not resampled.
    gx0, _, _, gy1 = desc.bounds
    minx = gx0 + ((minx - gx0) // res_x) * res_x
    maxy = gy1 - ((gy1 - maxy) // res_y) * res_y
    transform, width, height = grid_for_bounds((minx, miny, maxx, maxy), res_x, snap=False)
    ax, ay = desc.axis_labels[0], desc.axis_labels[1]

    async def fetch_chunk(bounds, w, h):
        x0, y0, x1, y1 = bounds
        params = [("service", "WCS"), ("version", "2.0.1"), ("request", "GetCoverage"),
                  ("coverageId", coverage_id), ("format", "image/tiff"),
                  ("subset", f"{ax}({x0},{x1})"), ("subset", f"{ay}({y0},{y1})")]
        body, content_type = await fetch_bytes_async(session, url, params)
        raise_if_error_document(body, content_type)
        raster = read_geotiff(body)
        return raster.data, raster.nodata

    array, nodata = await mosaic_async(transform, width, height, fetch_chunk, max_size, max_concurrency)
    return make_raster(array, nodata, desc.crs, transform, source="WCS", url=url, coverage_id=coverage_id)


def download_raster(url: str, coverage_id: str, north: float, west: float, south: float, east: float, path: str,
                    **kwargs) -> Raster:
    """
    Same as :func:`get_raster`, then saves the result (use ``.tif`` to keep the values).

    :param path: Output path.
    :return: The raster.
    """
    raster = get_raster(url, coverage_id, north, west, south, east, **kwargs)
    raster.save(path)
    return raster


def parse_coverage_description(xml: bytes, coverage_id: str) -> CoverageDescription:
    root = ET.fromstring(xml)
    envelope = next((e for e in root.iter() if _local(e.tag) == "Envelope"), None)
    if envelope is None:
        raise ServiceError(f"No envelope in the description of {coverage_id}")
    srs = envelope.get("srsName", "")
    match = re.search(r"EPSG/0/(\d+)|EPSG::?(\d+)", srs)
    if not match:
        raise ServiceError(f"Unsupported CRS {srs!r}")
    crs = f"EPSG:{match.group(1) or match.group(2)}"
    labels = (envelope.get("axisLabels") or "x y").split()
    lower = [float(v) for v in _text(envelope, "lowerCorner").split()]
    upper = [float(v) for v in _text(envelope, "upperCorner").split()]
    offsets = [[float(v) for v in e.text.split()] for e in root.iter() if _local(e.tag) == "offsetVector"]
    res = (abs(offsets[0][0]) or abs(offsets[0][1]), abs(offsets[1][1]) or abs(offsets[1][0])) if len(offsets) >= 2 \
        else (1.0, 1.0)
    # Envelopes follow the CRS axis order; convert to x/y.
    if labels[0].lower() in ("lat", "y", "n", "northing") and labels[1].lower() in ("long", "lon", "x", "e", "easting"):
        labels = [labels[1], labels[0]]
        lower, upper, res = lower[::-1], upper[::-1], res[::-1]
    return CoverageDescription(coverage_id=coverage_id, crs=crs, axis_labels=labels, resolution=res,
                               bounds=(lower[0], lower[1], upper[0], upper[1]))


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _text(element, name) -> str:
    for child in element:
        if _local(child.tag) == name:
            return child.text or ""
    return ""
