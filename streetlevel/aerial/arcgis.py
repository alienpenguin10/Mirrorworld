# SURVAI: added module (not upstream).
"""Requests against ArcGIS MapServer tile caches, shared by the Esri and USGS providers."""
from typing import Set, Tuple

from aiohttp import ClientSession

from .util import HEADERS, TILE_SIZE

TILEMAP_BLOCK = 64
"""Largest tilemap window the server answers without shrinking it."""


def build_tile_url(service_url: str, x: int, y: int, zoom: int) -> str:
    return f"{service_url}/tile/{zoom}/{y}/{x}"


def build_tilemap_url(service_url: str, x: int, y: int, zoom: int, width: int, height: int) -> str:
    return f"{service_url}/tilemap/{zoom}/{y}/{x}/{height}/{width}"


def tile_exists(service_url: str, x: int, y: int, zoom: int, session=None) -> bool:
    """
    Asks the tile cache whether a tile exists at this zoom level, without downloading it.
    """
    import requests
    requester = session if session else requests
    response = requester.get(build_tilemap_url(service_url, x, y, zoom, 1, 1), headers=HEADERS, timeout=60)
    if response.status_code != 200:
        # USGS answers 422 "Tiles not present" for zoom levels outside its cache.
        return False
    data = response.json()
    return bool(data.get("data") and data["data"][0])


async def tile_exists_async(service_url: str, x: int, y: int, zoom: int, session: ClientSession) -> bool:
    """
    Asks the tile cache whether a tile exists at this zoom level, without downloading it.
    """
    async with session.get(build_tilemap_url(service_url, x, y, zoom, 1, 1), headers=HEADERS) as response:
        if response.status != 200:
            # USGS answers 422 "Tiles not present" for zoom levels outside its cache.
            return False
        data = await response.json(content_type=None)
        return bool(data.get("data") and data["data"][0])


async def find_missing_tiles_async(service_url: str, left: int, top: int, right: int, bottom: int,
                                   zoom: int, session: ClientSession) -> Set[Tuple[int, int]]:
    """
    Lists the tiles inside a global pixel window that the cache does not have, using the tilemap endpoint,
    which answers for a block of up to 64x64 tiles per request.

    :return: X/Y coordinates of missing tiles.
    """
    tx0, ty0 = left // TILE_SIZE, top // TILE_SIZE
    tx1, ty1 = (right - 1) // TILE_SIZE, (bottom - 1) // TILE_SIZE
    missing = set()
    for by in range(ty0, ty1 + 1, TILEMAP_BLOCK):
        for bx in range(tx0, tx1 + 1, TILEMAP_BLOCK):
            width = min(TILEMAP_BLOCK, tx1 - bx + 1)
            height = min(TILEMAP_BLOCK, ty1 - by + 1)
            url = build_tilemap_url(service_url, bx, by, zoom, width, height)
            async with session.get(url, headers=HEADERS) as response:
                if response.status != 200:
                    missing.update((bx + i, by + j) for j in range(height) for i in range(width))
                    continue
                data = await response.json(content_type=None)
            flags = data.get("data") or []
            for j in range(height):
                for i in range(width):
                    k = j * width + i
                    if k >= len(flags) or not flags[k]:
                        missing.add((bx + i, by + j))
    return missing
