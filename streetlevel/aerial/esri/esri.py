# SURVAI: added module (not upstream).
"""Esri World Imagery (a mosaic of satellite and aerial imagery), worldwide."""
from typing import Optional

from PIL import Image
from aiohttp import ClientSession
from requests import Session

from . import api
from ..dataclasses import AerialImage
from ..util import TileResponse, bbox_to_pixels, get_tiled_image_async, run_sync, save_aerial_image, \
    tile_to_image, wgs84_to_pixel, TILE_SIZE, DEFAULT_MAX_TILES, DEFAULT_MAX_CONCURRENCY

PROVIDER = "Esri World Imagery"
MAX_ZOOM = 23


def get_tile(x: int, y: int, zoom: int, session: Session = None) -> Optional[Image.Image]:
    """
    Downloads one aerial tile.

    :param x: X coordinate of the tile.
    :param y: Y coordinate of the tile.
    :param zoom: Zoom level.
    :param session: *(optional)* A requests session.
    :return: The tile as PIL image, or None if Esri has no imagery for it at this zoom level.
    """
    if not api.tile_exists(x, y, zoom, session):
        return None
    response = api.get_tile(x, y, zoom, session)
    return None if _is_missing(response) else tile_to_image(response)


async def get_tile_async(x: int, y: int, zoom: int, session: ClientSession) -> Optional[Image.Image]:
    # Beyond its coverage the server returns a "Map data not yet available" placeholder with status 200,
    # so availability is checked with the tilemap endpoint first.
    if not await api.tile_exists_async(x, y, zoom, session):
        return None
    response = await api.get_tile_async(x, y, zoom, session)
    return None if _is_missing(response) else tile_to_image(response)


def find_max_zoom(lat: float, lon: float, session: Session = None) -> Optional[int]:
    """
    Finds the highest zoom level with imagery at a location.

    :param lat: Latitude.
    :param lon: Longitude.
    :param session: *(optional)* A requests session.
    :return: The zoom level, e.g. 19 (≈0.20 m/px) in Seattle, or None if there is no imagery.
    """
    for zoom in range(MAX_ZOOM, -1, -1):
        x, y = _tile_at(lat, lon, zoom)
        if api.tile_exists(x, y, zoom, session):
            return zoom
    return None


async def find_max_zoom_async(lat: float, lon: float, session: ClientSession) -> Optional[int]:
    for zoom in range(MAX_ZOOM, -1, -1):
        x, y = _tile_at(lat, lon, zoom)
        if await api.tile_exists_async(x, y, zoom, session):
            return zoom
    return None


def get_image(north: float, west: float, south: float, east: float, zoom: int = None,
              max_tiles: int = DEFAULT_MAX_TILES,
              max_concurrency: int = DEFAULT_MAX_CONCURRENCY) -> AerialImage:
    """
    Downloads the aerial imagery inside a bounding box and stitches it into one image.

    :param north: Latitude of the top edge.
    :param west: Longitude of the left edge.
    :param south: Latitude of the bottom edge.
    :param east: Longitude of the right edge.
    :param zoom: *(optional)* Zoom level. Defaults to the highest one available at the center of the box.
    :param max_tiles: *(optional)* Refuse requests covering more tiles than this. Defaults to 20000.
    :param max_concurrency: *(optional)* Maximum number of simultaneous requests. Defaults to 8.
    :return: The stitched image.
    """
    return run_sync(get_image_async, north, west, south, east, zoom=zoom, max_tiles=max_tiles,
                    max_concurrency=max_concurrency)


async def get_image_async(north: float, west: float, south: float, east: float, session: ClientSession,
                          zoom: int = None, max_tiles: int = DEFAULT_MAX_TILES,
                          max_concurrency: int = DEFAULT_MAX_CONCURRENCY) -> AerialImage:
    if zoom is None:
        zoom = await find_max_zoom_async((north + south) / 2, (west + east) / 2, session)
        if zoom is None:
            raise ValueError("No imagery at the center of the bounding box")
    left, top, right, bottom = bbox_to_pixels(north, west, south, east, zoom)
    missing = await api.find_missing_tiles_async(left, top, right, bottom, zoom, session)
    return await get_tiled_image_async(
        north, west, south, east, zoom, PROVIDER,
        lambda x, y: api.build_tile_url(x, y, zoom), _is_missing, session,
        skip_tiles=missing, max_tiles=max_tiles, max_concurrency=max_concurrency)


def download_image(north: float, west: float, south: float, east: float, path: str, zoom: int = None,
                   pil_args: dict = None, max_tiles: int = DEFAULT_MAX_TILES,
                   max_concurrency: int = DEFAULT_MAX_CONCURRENCY) -> AerialImage:
    """
    Downloads the aerial imagery inside a bounding box to a georeferenced file
    (world file, ``.aux.xml`` and ``.json`` beside it; see :func:`streetlevel.aerial.util.save_aerial_image`).

    :param north: Latitude of the top edge.
    :param west: Longitude of the left edge.
    :param south: Latitude of the bottom edge.
    :param east: Longitude of the right edge.
    :param path: Output path.
    :param zoom: *(optional)* Zoom level. Defaults to the highest one available at the center of the box.
    :param pil_args: *(optional)* Additional arguments for PIL's ``Image.save`` method.
    :param max_tiles: *(optional)* Refuse requests covering more tiles than this. Defaults to 20000.
    :param max_concurrency: *(optional)* Maximum number of simultaneous requests. Defaults to 8.
    :return: The stitched image.
    """
    aerial = get_image(north, west, south, east, zoom, max_tiles, max_concurrency)
    save_aerial_image(aerial, path, pil_args)
    return aerial


async def download_image_async(north: float, west: float, south: float, east: float, path: str,
                               session: ClientSession, zoom: int = None, pil_args: dict = None,
                               max_tiles: int = DEFAULT_MAX_TILES,
                               max_concurrency: int = DEFAULT_MAX_CONCURRENCY) -> AerialImage:
    aerial = await get_image_async(north, west, south, east, session, zoom, max_tiles, max_concurrency)
    save_aerial_image(aerial, path, pil_args)
    return aerial


def _is_missing(response: TileResponse) -> bool:
    return response.status == 404


def _tile_at(lat: float, lon: float, zoom: int):
    px, py = wgs84_to_pixel(lat, lon, zoom)
    return int(px // TILE_SIZE), int(py // TILE_SIZE)
