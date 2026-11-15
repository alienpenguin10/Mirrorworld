# Mirrorworld addition (not in upstream streetlevel).
"""
AHN (Actueel Hoogtebestand Nederland), the Dutch national LiDAR elevation model, 0.5 m, via PDOK's WCS.
Open data (CC0), no key. Heights in meters above NAP, in the Dutch national grid (EPSG:28992).
"""
import numpy as np
from aiohttp import ClientSession

from ..raster import Raster
from ..services import wcs

WCS_URL = "https://service.pdok.nl/rws/ahn/wcs/v1_0"


def get_dsm(north: float, west: float, south: float, east: float) -> Raster:
    """
    Downloads the digital surface model (top of buildings, trees, poles, ...) for a bounding box.

    :param north: Latitude of the top edge.
    :param west: Longitude of the left edge.
    :param south: Latitude of the bottom edge.
    :param east: Longitude of the right edge.
    :return: A float32 raster in meters above NAP; water and gaps are ``nodata``.
    """
    return _tag(wcs.get_raster(WCS_URL, "dsm_05m", north, west, south, east), "dsm")


async def get_dsm_async(north: float, west: float, south: float, east: float, session: ClientSession) -> Raster:
    return _tag(await wcs.get_raster_async(WCS_URL, "dsm_05m", north, west, south, east, session), "dsm")


def get_dtm(north: float, west: float, south: float, east: float) -> Raster:
    """
    Downloads the digital terrain model (bare ground) for a bounding box.

    :param north: Latitude of the top edge.
    :param west: Longitude of the left edge.
    :param south: Latitude of the bottom edge.
    :param east: Longitude of the right edge.
    :return: A float32 raster in meters above NAP; buildings and water are ``nodata``.
    """
    return _tag(wcs.get_raster(WCS_URL, "dtm_05m", north, west, south, east), "dtm")


async def get_dtm_async(north: float, west: float, south: float, east: float, session: ClientSession) -> Raster:
    return _tag(await wcs.get_raster_async(WCS_URL, "dtm_05m", north, west, south, east, session), "dtm")


def get_ndsm(north: float, west: float, south: float, east: float) -> Raster:
    """
    Computes object heights above ground (surface model minus terrain model), e.g. for pole, tree and building
    heights. Where the terrain model has gaps (under buildings), the lowest terrain height in the box is used.

    :param north: Latitude of the top edge.
    :param west: Longitude of the left edge.
    :param south: Latitude of the bottom edge.
    :param east: Longitude of the right edge.
    :return: A float32 raster of heights above ground in meters.
    """
    return compute_ndsm(get_dsm(north, west, south, east), get_dtm(north, west, south, east))


async def get_ndsm_async(north: float, west: float, south: float, east: float, session: ClientSession) -> Raster:
    return compute_ndsm(await get_dsm_async(north, west, south, east, session),
                        await get_dtm_async(north, west, south, east, session))


def download_dsm(north: float, west: float, south: float, east: float, path: str) -> Raster:
    """Same as :func:`get_dsm`, then saves the result (use ``.tif`` to keep the values)."""
    raster = get_dsm(north, west, south, east)
    raster.save(path)
    return raster


def download_dtm(north: float, west: float, south: float, east: float, path: str) -> Raster:
    """Same as :func:`get_dtm`, then saves the result (use ``.tif`` to keep the values)."""
    raster = get_dtm(north, west, south, east)
    raster.save(path)
    return raster


def download_ndsm(north: float, west: float, south: float, east: float, path: str) -> Raster:
    """Same as :func:`get_ndsm`, then saves the result (use ``.tif`` to keep the values)."""
    raster = get_ndsm(north, west, south, east)
    raster.save(path)
    return raster


def compute_ndsm(dsm: Raster, dtm: Raster) -> Raster:
    """Subtracts a terrain model from a surface model on the same grid."""
    if dsm.data.shape != dtm.data.shape:
        raise ValueError("DSM and DTM grids differ")
    surface = dsm.data[0].astype(np.float32)
    ground = dtm.data[0].astype(np.float32)
    surface_valid = surface != dsm.nodata if dsm.nodata is not None else np.isfinite(surface)
    ground_valid = ground != dtm.nodata if dtm.nodata is not None else np.isfinite(ground)
    fallback = float(np.min(ground[ground_valid])) if ground_valid.any() else 0.0
    ground = np.where(ground_valid, ground, fallback)
    nodata = -9999.0
    height = np.where(surface_valid, surface - ground, nodata).astype(np.float32)
    return Raster(data=height[np.newaxis], crs=dsm.crs, transform=dsm.transform, nodata=nodata,
                  band_names=["height_above_ground"],
                  metadata={**dsm.metadata, "product": "ndsm", "provider": "AHN via PDOK", "license": "CC0"})


def _tag(raster: Raster, product: str) -> Raster:
    raster.band_names = [product]
    raster.metadata.update({"product": product, "provider": "AHN via PDOK", "license": "CC0", "unit": "m above NAP"})
    return raster
