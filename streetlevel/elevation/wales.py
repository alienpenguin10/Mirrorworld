# Mirrorworld addition (not in upstream streetlevel).
"""
Welsh Government / Natural Resources Wales LiDAR elevation models for Wales, 1 m, read straight from the national
cloud-optimized GeoTIFFs published on Data Map Wales (DataMapWales). Open Government Licence v3, no key.
Heights in meters above Ordnance Datum Newlyn, in the British National Grid (EPSG:27700).
"""
import numpy as np

from .ahn import compute_ndsm
from ..raster import Raster, read_cog

DSM_URL = "https://dmwproductionblob.blob.core.windows.net/cogs/lidar/wales_dsm_32bit_cog.tif"
DTM_URL = "https://dmwproductionblob.blob.core.windows.net/cogs/lidar/wales_dtm_32bit_cog.tif"


def get_dsm(north: float, west: float, south: float, east: float) -> Raster:
    """
    Reads the 1 m surface model (top of buildings, trees, ...) for a bounding box in Wales.

    :param north: Latitude of the top edge.
    :param west: Longitude of the left edge.
    :param south: Latitude of the bottom edge.
    :param east: Longitude of the right edge.
    :return: A float32 raster in meters (EPSG:27700).
    :raises ValueError: If the box has no Welsh LiDAR data.
    """
    return _tag(read_cog(DSM_URL, north, west, south, east), "dsm", DSM_URL)


def get_dtm(north: float, west: float, south: float, east: float) -> Raster:
    """
    Reads the 1 m terrain model (bare ground) for a bounding box in Wales.

    :param north: Latitude of the top edge.
    :param west: Longitude of the left edge.
    :param south: Latitude of the bottom edge.
    :param east: Longitude of the right edge.
    :return: A float32 raster in meters (EPSG:27700).
    :raises ValueError: If the box has no Welsh LiDAR data.
    """
    return _tag(read_cog(DTM_URL, north, west, south, east), "dtm", DTM_URL)


def get_ndsm(north: float, west: float, south: float, east: float) -> Raster:
    """
    Computes object heights above ground (DSM minus DTM) for a bounding box in Wales.

    :return: A float32 raster of heights above ground in meters.
    """
    raster = compute_ndsm(get_dsm(north, west, south, east), get_dtm(north, west, south, east))
    raster.metadata.update({"provider": "Welsh Government / Natural Resources Wales",
                            "license": "Open Government Licence v3.0"})
    return raster


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


def _tag(raster: Raster, product: str, url: str) -> Raster:
    values = raster.data[0]
    valid = np.isfinite(values)
    if raster.nodata is not None:
        valid &= values != raster.nodata
    if not valid.any():
        raise ValueError("No Welsh LiDAR data in this box (the models cover Wales only)")
    raster.band_names = [product]
    raster.metadata.update({"product": product, "provider": "Welsh Government / Natural Resources Wales",
                            "license": "Open Government Licence v3.0", "unit": "m above Ordnance Datum Newlyn",
                            "url": url})
    return raster
