# Mirrorworld addition (not in upstream streetlevel).
"""
USGS 3D Elevation Program (3DEP) bare-earth DEM for the United States, from the best available source at each
place (1 m LiDAR-derived where it exists, else 1/3 or 1 arc-second). Public domain, no key.
For LiDAR point clouds see :mod:`mirrorworld.lidar.usgs3dep`.
"""
from typing import Optional

from aiohttp import ClientSession

from ..raster import Raster, utm_crs
from ..services import arcgis

IMAGE_SERVER = "https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer"


def get_dem(north: float, west: float, south: float, east: float, resolution: float = 1.0,
            crs: Optional[str] = None, max_size: int = 2000) -> Raster:
    """
    Downloads the bare-earth elevation model for a bounding box.

    :param north: Latitude of the top edge.
    :param west: Longitude of the left edge.
    :param south: Latitude of the bottom edge.
    :param east: Longitude of the right edge.
    :param resolution: *(optional)* Pixel size in meters. Defaults to 1.
    :param crs: *(optional)* Output CRS. Defaults to the UTM zone of the box center.
    :param max_size: *(optional)* Largest chunk side in pixels. Defaults to 2000.
    :return: A float32 raster of elevations in meters (NAVD88).
    :raises ValueError: If there is no 3DEP data in the box.
    """
    crs = crs or utm_crs((north + south) / 2, (west + east) / 2)
    return _tag(arcgis.get_raster(IMAGE_SERVER, north, west, south, east, resolution, crs=crs, pixel_type="F32",
                                  max_size=max_size))


async def get_dem_async(north: float, west: float, south: float, east: float, session: ClientSession,
                        resolution: float = 1.0, crs: Optional[str] = None, max_size: int = 2000) -> Raster:
    crs = crs or utm_crs((north + south) / 2, (west + east) / 2)
    return _tag(await arcgis.get_raster_async(IMAGE_SERVER, north, west, south, east, session, resolution, crs=crs,
                                              pixel_type="F32", max_size=max_size))


def download_dem(north: float, west: float, south: float, east: float, path: str, **kwargs) -> Raster:
    """Same as :func:`get_dem`, then saves the result (use ``.tif`` to keep the values)."""
    raster = get_dem(north, west, south, east, **kwargs)
    raster.save(path)
    return raster


def _tag(raster: Raster) -> Raster:
    values = raster.data
    if raster.nodata is not None:
        values = values[values != raster.nodata]
    if values.size == 0 or (values == 0).all():
        # Outside its coverage the service answers with zeros rather than an error.
        raise ValueError("No 3DEP elevation data in this box; 3DEP covers the United States and territories")
    raster.band_names = ["elevation"]
    raster.metadata.update({"product": "dem", "provider": "USGS 3DEP", "license": "Public domain",
                            "unit": "m (NAVD88)"})
    return raster
