# SURVAI: added module (not upstream).
from aiohttp import ClientSession
from requests import Session

from ..util import TileResponse, get_tile_response, get_tile_response_async


def build_tile_url(x: int, y: int, zoom: int) -> str:
    # lyrs=s: satellite/aerial without labels.
    return f"https://mt{(x + y) % 4}.google.com/vt/lyrs=s&x={x}&y={y}&z={zoom}"


def get_tile(x: int, y: int, zoom: int, session: Session = None) -> TileResponse:
    return get_tile_response(build_tile_url(x, y, zoom), x, y, session)


async def get_tile_async(x: int, y: int, zoom: int, session: ClientSession) -> TileResponse:
    return await get_tile_response_async(build_tile_url(x, y, zoom), x, y, session)
