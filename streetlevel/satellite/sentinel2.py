# Mirrorworld addition (not in upstream streetlevel).
"""
Sentinel-2 Level-2A surface reflectance (ESA Copernicus), 10-60 m, 13 bands, every ~5 days worldwide,
from the Earth Search catalogue (Element 84, AWS open data). Free, no key.

Values are scaled reflectance; ``metadata["band_info"]`` gives the scale and offset to convert them
(reflectance = value * scale + offset). Band names: coastal, blue, green, red, rededge1-3, nir, nir08, nir09,
swir16, swir22, scl (scene classification, incl. clouds and shadows).
"""
from datetime import datetime
from typing import List, Optional, Sequence, Union

import numpy as np
from aiohttp import ClientSession

from ..satellite import stac
from ..satellite.scene import Scene
from ..raster import Raster

ENDPOINT = stac.EARTH_SEARCH
COLLECTION = "sentinel-2-l2a"
DEFAULT_BANDS = ("red", "green", "blue", "nir")
LICENSE = "Copernicus Sentinel data, free and open"


def find_scenes(north: float, west: float, south: float, east: float, start: Union[str, datetime, None] = None,
                end: Union[str, datetime, None] = None,
                max_cloud_cover: Optional[float] = 20, limit: int = 50) -> List[Scene]:
    """
    Finds Sentinel-2 scenes intersecting a bounding box, newest first.

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
               resolution: Optional[float] = 10.0, crs: Optional[str] = None,
               start: Union[str, datetime, None] = None, end: Union[str, datetime, None] = None,
                max_cloud_cover: Optional[float] = 20,
               resampling: str = "nearest", max_local_cloud: float = 0.1) -> Raster:
    """
    Reads Sentinel-2 bands for a bounding box.

    :param north: Latitude of the top edge.
    :param west: Longitude of the left edge.
    :param south: Latitude of the bottom edge.
    :param east: Longitude of the right edge.
    :param scenes: *(optional)* Scene(s) from :func:`find_scenes`. Defaults to the newest acquisition covering
        the box within ``start``/``end`` and under ``max_cloud_cover``.
    :param bands: *(optional)* Band names, e.g. ``nir`` and ``red`` for NDVI or ``scl`` for the cloud mask. Defaults to ``("red", "green", "blue", "nir")``.
    :param resolution: *(optional)* Pixel size in meters. Defaults to 10 (the native resolution of the visible and near-infrared bands).
    :param crs: *(optional)* Output CRS. Defaults to the scene's native CRS (UTM).
    :param start: *(optional)* Earliest acquisition date when choosing a scene.
    :param end: *(optional)* Latest acquisition date when choosing a scene.
    :param max_cloud_cover: *(optional)* Maximum cloud cover in percent. Defaults to 20.
    :param resampling: *(optional)* Resampling method. Defaults to ``nearest``.
    :param max_local_cloud: *(optional)* When choosing a scene, the largest cloudy fraction (0..1) allowed
        inside the box itself, judged from the scene classification classes 3 (cloud shadow), 8-9 (cloud) and 10 (cirrus). Defaults to 0.1.
    :return: A Raster; ``metadata`` names the scenes and any scale/offset per band.
    """
    if scenes is None:
        found = find_scenes(north, west, south, east, start, end, max_cloud_cover=max_cloud_cover, limit=50)
        scenes = stac.pick_clear_scenes(found, north, west, south, east, "scl", _is_cloud, max_local_cloud)
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


def _is_cloud(scl):
    return np.isin(scl, (3, 8, 9, 10))
