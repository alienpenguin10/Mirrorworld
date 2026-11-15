# SURVAI: added module (not upstream).
from typing import Set, Tuple

from aiohttp import ClientSession
from requests import Session

from .. import arcgis
from ..util import TileResponse, get_tile_response, get_tile_response_async

SERVICE_URL = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer"


def build_tile_url(x: int, y: int, zoom: int) -> str:
    return arcgis.build_tile_url(SERVICE_URL, x, y, zoom)


def get_tile(x: int, y: int, zoom: int, session: Session = None) -> TileResponse:
    return get_tile_response(build_tile_url(x, y, zoom), x, y, session)


async def get_tile_async(x: int, y: int, zoom: int, session: ClientSession) -> TileResponse:
    return await get_tile_response_async(build_tile_url(x, y, zoom), x, y, session)


def tile_exists(x: int, y: int, zoom: int, session: Session = None) -> bool:
    return arcgis.tile_exists(SERVICE_URL, x, y, zoom, session)


async def tile_exists_async(x: int, y: int, zoom: int, session: ClientSession) -> bool:
    return await arcgis.tile_exists_async(SERVICE_URL, x, y, zoom, session)


async def find_missing_tiles_async(left: int, top: int, right: int, bottom: int, zoom: int,
                                   session: ClientSession) -> Set[Tuple[int, int]]:
    return await arcgis.find_missing_tiles_async(SERVICE_URL, left, top, right, bottom, zoom, session)
