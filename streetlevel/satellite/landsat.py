# Mirrorworld addition (not in upstream streetlevel).
"""
Landsat Collection 2 Level-2 (USGS), 30 m surface reflectance and 100 m thermal (resampled to 30 m)
surface temperature, Landsat 4-9 since 1982, from Microsoft Planetary Computer. Free, no key.

Band names: coastal, blue, green, red, nir08, swir16, swir22, lwir11 (surface temperature; Landsat 8/9), qa_pixel.
Values are scaled; ``metadata["band_info"]`` gives scale and offset (temperature in kelvin = value * scale + offset).
"""
from datetime import datetime
from typing import List, Optional, Sequence, Union

import numpy as np
from aiohttp import ClientSession

from ..satellite import stac
from ..satellite.scene import Scene
from ..raster import Raster

ENDPOINT = stac.PLANETARY_COMPUTER
COLLECTION = "landsat-c2-l2"
DEFAULT_BANDS = ("red", "green", "blue", "nir08")
LICENSE = "USGS Landsat, public domain"


def find_scenes(north: float, west: float, south: float, east: float, start: Union[str, datetime, None] = None,
                end: Union[str, datetime, None] = None,
                max_cloud_cover: Optional[float] = 20, limit: int = 50) -> List[Scene]:
    """
    Finds Landsat scenes intersecting a bounding box, newest first.

    :param north: Latitude of the top edge.
    :param west: Longitude of the left edge.
    :param south: Latitude of the bottom edge.
    :param east: Longitude of the right edge.
    :param start: *(optional)* Earliest acquisition date, e.g. ``"2024-06-01"``.
    :param end: *(optional)* Latest acquisition date (inclusive).
    :param max_cloud_cover: *(optional)* Maximum cloud cover in percent. Defaults to 20.
    :param limit: *(optional)* Maximum number of scenes. Defaults to 50.
    :return: A list of Scene objects.
    """
    return stac.search(ENDPOINT, COLLECTION, north, west, south, east, start, end, max_cloud_cover, limit=limit)


async def find_scenes_async(north: float, west: float, south: float, east: float, session: ClientSession,
                            start: Union[str, datetime, None] = None, end: Union[str, datetime, None] = None,
                max_cloud_cover: Optional[float] = 20,
                            limit: int = 50) -> List[Scene]:
    return await stac.search_async(ENDPOINT, COLLECTION, north, west, south, east, session, start, end,
                                   max_cloud_cover, limit=limit)


def get_raster(north: float, west: float, south: float, east: float,
               scenes: Union[Scene, Sequence[Scene], None] = None, bands: Sequence[str] = DEFAULT_BANDS,
               resolution: Optional[float] = 30.0, crs: Optional[str] = None,
               start: Union[str, datetime, None] = None, end: Union[str, datetime, None] = None,
                max_cloud_cover: Optional[float] = 20,
               resampling: str = "nearest", max_local_cloud: float = 0.1) -> Raster:
    """
    Reads Landsat bands for a bounding box.

    :param north: Latitude of the top edge.
    :param west: Longitude of the left edge.
    :param south: Latitude of the bottom edge.
    :param east: Longitude of the right edge.
    :param scenes: *(optional)* Scene(s) from :func:`find_scenes`. Defaults to the newest acquisition covering
        the box within ``start``/``end`` and under ``max_cloud_cover``.
    :param bands: *(optional)* Band names, e.g. ``lwir11`` for surface temperature. Defaults to ``("red", "green", "blue", "nir08")``.
    :param resolution: *(optional)* Pixel size in meters. Defaults to 30.
    :param crs: *(optional)* Output CRS. Defaults to the scene's native CRS (UTM).
    :param start: *(optional)* Earliest acquisition date when choosing a scene.
    :param end: *(optional)* Latest acquisition date when choosing a scene.
    :param max_cloud_cover: *(optional)* Maximum cloud cover in percent. Defaults to 20.
    :param resampling: *(optional)* Resampling method. Defaults to ``nearest``.
    :param max_local_cloud: *(optional)* When choosing a scene, the largest cloudy fraction (0..1) allowed
        inside the box itself, judged from the QA_PIXEL bits 1-4 (dilated cloud, cirrus, cloud, cloud shadow). Defaults to 0.1.
    :return: A Raster; ``metadata`` names the scenes and any scale/offset per band.
    """
    if scenes is None:
        found = find_scenes(north, west, south, east, start, end, max_cloud_cover=max_cloud_cover, limit=50)
        scenes = stac.pick_clear_scenes(found, north, west, south, east, "qa_pixel", _is_cloud, max_local_cloud)
    raster = stac.read(scenes, bands, north, west, south, east, resolution=resolution, crs=crs,
                       resampling=resampling)
    raster.metadata["license"] = LICENSE
    return raster


def download_raster(north: float, west: float, south: float, east: float, path: str, **kwargs) -> Raster:
    """
    Same as :func:`get_raster`, then saves the result (``.tif`` keeps all bands and values).

    :param path: Output path.
    :return: The raster.
    """
    raster = get_raster(north, west, south, east, **kwargs)
    raster.save(path)
    return raster


def _is_cloud(qa):
    return (qa.astype(np.uint32) & 0b11110) != 0
