# Mirrorworld addition (not in upstream streetlevel).
"""
Environment Agency LiDAR composite elevation models for England, 1 m, via the Defra Data Services Platform WCS:
the terrain model (DTM, bare ground, 2022 composite) and the first-return surface model (FZ_DSM, top of trees,
buildings, wires and poles). Open Government Licence v3, no key. Heights in meters above Ordnance Datum Newlyn,
in the British National Grid (EPSG:27700).

The services occasionally stall single requests; the client retries them, so a box can take tens of seconds.
Outside England the service returns zeros: boxes with no data raise ``ValueError``, but in boxes straddling the
border the pixels outside England are 0 rather than nodata.
"""
from typing import Optional

from aiohttp import ClientSession

from .ahn import compute_ndsm
from ..raster import Raster
from ..services import wcs

DTM_URL = "https://environment.data.gov.uk/spatialdata/lidar-composite-digital-terrain-model-dtm-1m-2022/wcs"
DSM_URL = "https://environment.data.gov.uk/spatialdata/lidar-composite-digital-surface-model-first-return-dsm-1m/wcs"
DTM_SUFFIX = "__Lidar_Composite_Elevation_DTM_1m"
DSM_SUFFIX = "__Lidar_Composite_Elevation_FZ_DSM_1m"
_coverage_ids = {}


def get_dtm(north: float, west: float, south: float, east: float) -> Raster:
    """
    Downloads the 1 m terrain model (bare ground) for a bounding box in England.

    :param north: Latitude of the top edge.
    :param west: Longitude of the left edge.
    :param south: Latitude of the bottom edge.
    :param east: Longitude of the right edge.
    :return: A float32 raster in meters above Ordnance Datum Newlyn (EPSG:27700).
    :raises ValueError: If the box is outside the coverage.
    """
    return _tag(wcs.get_raster(DTM_URL, _coverage_id(DTM_URL, DTM_SUFFIX), north, west, south, east), "dtm")


async def get_dtm_async(north: float, west: float, south: float, east: float, session: ClientSession) -> Raster:
    coverage = await _coverage_id_async(DTM_URL, DTM_SUFFIX, session)
    return _tag(await wcs.get_raster_async(DTM_URL, coverage, north, west, south, east, session), "dtm")


def get_dsm(north: float, west: float, south: float, east: float) -> Raster:
    """
    Downloads the 1 m first-return surface model (top of buildings, trees, poles, wires) for a bounding box in
    England.

    :param north: Latitude of the top edge.
    :param west: Longitude of the left edge.
    :param south: Latitude of the bottom edge.
    :param east: Longitude of the right edge.
    :return: A float32 raster in meters above Ordnance Datum Newlyn (EPSG:27700).
    :raises ValueError: If the box is outside the coverage.
    """
    return _tag(wcs.get_raster(DSM_URL, _coverage_id(DSM_URL, DSM_SUFFIX), north, west, south, east), "dsm")


async def get_dsm_async(north: float, west: float, south: float, east: float, session: ClientSession) -> Raster:
    coverage = await _coverage_id_async(DSM_URL, DSM_SUFFIX, session)
    return _tag(await wcs.get_raster_async(DSM_URL, coverage, north, west, south, east, session), "dsm")


def get_ndsm(north: float, west: float, south: float, east: float) -> Raster:
    """
    Computes object heights above ground (first-return DSM minus DTM), e.g. for tree, building and pole heights.

    :param north: Latitude of the top edge.
    :param west: Longitude of the left edge.
    :param south: Latitude of the bottom edge.
    :param east: Longitude of the right edge.
    :return: A float32 raster of heights above ground in meters.
    """
    return _relabel(compute_ndsm(get_dsm(north, west, south, east), get_dtm(north, west, south, east)))


async def get_ndsm_async(north: float, west: float, south: float, east: float, session: ClientSession) -> Raster:
    return _relabel(compute_ndsm(await get_dsm_async(north, west, south, east, session),
                                 await get_dtm_async(north, west, south, east, session)))


def download_dtm(north: float, west: float, south: float, east: float, path: str) -> Raster:
    """Same as :func:`get_dtm`, then saves the result (use ``.tif`` to keep the values)."""
    raster = get_dtm(north, west, south, east)
    raster.save(path)
    return raster


def download_dsm(north: float, west: float, south: float, east: float, path: str) -> Raster:
    """Same as :func:`get_dsm`, then saves the result (use ``.tif`` to keep the values)."""
    raster = get_dsm(north, west, south, east)
    raster.save(path)
    return raster


def download_ndsm(north: float, west: float, south: float, east: float, path: str) -> Raster:
    """Same as :func:`get_ndsm`, then saves the result (use ``.tif`` to keep the values)."""
    raster = get_ndsm(north, west, south, east)
    raster.save(path)
    return raster


def _coverage_id(url: str, suffix: str) -> str:
    # Coverage IDs carry a UUID that changes when the data is republished, so look them up by name.
    if url not in _coverage_ids:
        _coverage_ids[url] = _pick(wcs.get_coverage_ids(url), suffix, url)
    return _coverage_ids[url]


async def _coverage_id_async(url: str, suffix: str, session: ClientSession) -> str:
    if url not in _coverage_ids:
        _coverage_ids[url] = _pick(await wcs.get_coverage_ids_async(url, session), suffix, url)
    return _coverage_ids[url]


def _pick(ids, suffix, url) -> str:
    for coverage in ids:
        if coverage.endswith(suffix):
            return coverage
    raise ValueError(f"No coverage ending in {suffix} at {url}; available: {ids}")


def _tag(raster: Raster, product: str) -> Raster:
    values = raster.data[0]
    if raster.nodata is not None:
        values = values[values != raster.nodata]
    if values.size == 0 or (values == 0).all():
        # Outside England the service answers with zeros rather than nodata.
        raise ValueError("No Environment Agency LiDAR data in this box (the composites cover England only)")
    raster.band_names = [product]
    raster.metadata.update({"product": product, "provider": "Environment Agency (Defra)",
                            "license": "Open Government Licence v3.0", "unit": "m above Ordnance Datum Newlyn"})
    return raster


def _relabel(raster: Raster) -> Raster:
    raster.metadata.update({"provider": "Environment Agency (Defra)", "license": "Open Government Licence v3.0"})
    return raster
