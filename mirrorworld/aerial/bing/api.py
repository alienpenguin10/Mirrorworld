# Mirrorworld addition (not in upstream streetlevel).
from aiohttp import ClientSession
from requests import Session

from .util import to_quadkey
from ..util import TileResponse, get_tile_response, get_tile_response_async

DEFAULT_GENERATION = 15000
"""Imagery generation (``g`` parameter). Requests without one are rejected with HTTP 400."""


def build_tile_url(x: int, y: int, zoom: int, generation: int = DEFAULT_GENERATION) -> str:
    return f"https://ecn.t{(x + y) % 4}.tiles.virtualearth.net/tiles/a{to_quadkey(x, y, zoom)}.jpeg" \
           f"?g={generation}"


def get_tile(x: int, y: int, zoom: int, session: Session = None) -> TileResponse:
    return get_tile_response(build_tile_url(x, y, zoom), x, y, session)


async def get_tile_async(x: int, y: int, zoom: int, session: ClientSession) -> TileResponse:
    return await get_tile_response_async(build_tile_url(x, y, zoom), x, y, session)
