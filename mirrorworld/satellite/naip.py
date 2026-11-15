# Mirrorworld addition (not in upstream streetlevel).
"""
NAIP (USDA National Agriculture Imagery Program) aerial imagery of the contiguous United States, 0.6 m
(1 m before ~2018) with red, green, blue and near-infrared bands, every 2-3 years per state, from
Microsoft Planetary Computer. Public domain, no key.
"""
from datetime import datetime
from typing import List, Optional, Sequence, Union

from aiohttp import ClientSession

from ..satellite import stac
from ..satellite.scene import Scene
from ..raster import Raster

ENDPOINT = stac.PLANETARY_COMPUTER
COLLECTION = "naip"
DEFAULT_BANDS = ("image",)
LICENSE = "USDA NAIP, public domain"


def find_scenes(north: float, west: float, south: float, east: float, start: Union[str, datetime, None] = None,
                end: Union[str, datetime, None] = None, limit: int = 50) -> List[Scene]:
    """
    Finds NAIP tiles intersecting a bounding box, newest first.

    :param north: Latitude of the top edge.
    :param west: Longitude of the left edge.
    :param south: Latitude of the bottom edge.
    :param east: Longitude of the right edge.
    :param start: *(optional)* Earliest acquisition date, e.g. ``"2024-06-01"``.
    :param end: *(optional)* Latest acquisition date (inclusive).
    :param limit: *(optional)* Maximum number of scenes. Defaults to 50.
    :return: A list of Scene objects.
    """
    return stac.search(ENDPOINT, COLLECTION, north, west, south, east, start, end, None, limit=limit)


async def find_scenes_async(north: float, west: float, south: float, east: float, session: ClientSession,
                            start: Union[str, datetime, None] = None, end: Union[str, datetime, None] = None,
                            limit: int = 50) -> List[Scene]:
    return await stac.search_async(ENDPOINT, COLLECTION, north, west, south, east, session, start, end,
                                   None, limit=limit)


def get_raster(north: float, west: float, south: float, east: float,
               scenes: Union[Scene, Sequence[Scene], None] = None, bands: Sequence[str] = DEFAULT_BANDS,
               resolution: Optional[float] = None, crs: Optional[str] = None,
               start: Union[str, datetime, None] = None, end: Union[str, datetime, None] = None,
               resampling: str = "nearest") -> Raster:
    """
    Reads NAIP imagery (red, green, blue, nir) for a bounding box.

    :param north: Latitude of the top edge.
    :param west: Longitude of the left edge.
    :param south: Latitude of the bottom edge.
    :param east: Longitude of the right edge.
    :param scenes: *(optional)* Scene(s) from :func:`find_scenes`. Defaults to the newest acquisition covering
        the box within ``start``/``end``.
    :param bands: *(optional)* Asset names; ``image`` holds all four bands. Defaults to ``("image",)``.
    :param resolution: *(optional)* Pixel size in meters. Defaults to the native resolution (0.6 m for recent years).
    :param crs: *(optional)* Output CRS. Defaults to the scene's native CRS (UTM, NAD83).
    :param start: *(optional)* Earliest acquisition date when choosing a scene.
    :param end: *(optional)* Latest acquisition date when choosing a scene.
    :param resampling: *(optional)* Resampling method. Defaults to ``nearest``.
    :return: A Raster; ``metadata`` names the scenes and any scale/offset per band.
    """
    if scenes is None:
        found = find_scenes(north, west, south, east, start, end, limit=50)
        scenes = stac.pick_scenes(found, north, west, south, east)
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
