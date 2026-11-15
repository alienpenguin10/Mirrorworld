# Mirrorworld addition (not in upstream streetlevel).
"""Bing Maps aerial imagery, worldwide."""
from typing import Optional

from PIL import Image
from aiohttp import ClientSession
from requests import Session

from . import api
from ..dataclasses import AerialImage
from ..util import TileResponse, get_tiled_image_async, run_sync, save_aerial_image, tile_to_image, \
    get_header, wgs84_to_pixel, TILE_SIZE, DEFAULT_MAX_TILES, DEFAULT_MAX_CONCURRENCY

PROVIDER = "Bing Maps"
MAX_ZOOM = 21
METADATA_HEADERS = ("X-VE-TILEMETA-CaptureDatesRange", "X-VE-TILEMETA-Product-IDs")


def get_tile(x: int, y: int, zoom: int, session: Session = None) -> Optional[Image.Image]:
    """
    Downloads one aerial tile.

    :param x: X coordinate of the tile.
    :param y: Y coordinate of the tile.
    :param zoom: Zoom level.
    :param session: *(optional)* A requests session.
    :return: The tile as PIL image, or None if Bing has no imagery for it at this zoom level.
    """
    response = api.get_tile(x, y, zoom, session)
    return None if _is_missing(response) else tile_to_image(response)


async def get_tile_async(x: int, y: int, zoom: int, session: ClientSession) -> Optional[Image.Image]:
    response = await api.get_tile_async(x, y, zoom, session)
    return None if _is_missing(response) else tile_to_image(response)


def find_max_zoom(lat: float, lon: float, session: Session = None) -> Optional[int]:
    """
    Finds the highest zoom level with imagery at a location.

    :param lat: Latitude.
    :param lon: Longitude.
    :param session: *(optional)* A requests session.
    :return: The zoom level, e.g. 20 (≈0.10 m/px) in Seattle, or None if there is no imagery.
    """
    for zoom in range(MAX_ZOOM, 0, -1):
        x, y = _tile_at(lat, lon, zoom)
        if not _is_missing(api.get_tile(x, y, zoom, session)):
            return zoom
    return None


async def find_max_zoom_async(lat: float, lon: float, session: ClientSession) -> Optional[int]:
    for zoom in range(MAX_ZOOM, 0, -1):
        x, y = _tile_at(lat, lon, zoom)
        if not _is_missing(await api.get_tile_async(x, y, zoom, session)):
            return zoom
    return None


def get_image(north: float, west: float, south: float, east: float, zoom: int = None,
              max_tiles: int = DEFAULT_MAX_TILES,
              max_concurrency: int = DEFAULT_MAX_CONCURRENCY) -> AerialImage:
    """
    Downloads the aerial imagery inside a bounding box and stitches it into one image.

    Capture date ranges reported by Bing are collected in ``AerialImage.metadata``.

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
    return await get_tiled_image_async(
        north, west, south, east, zoom, PROVIDER,
        lambda x, y: api.build_tile_url(x, y, zoom), _is_missing, session,
        metadata_headers=METADATA_HEADERS, max_tiles=max_tiles, max_concurrency=max_concurrency)


def download_image(north: float, west: float, south: float, east: float, path: str, zoom: int = None,
                   pil_args: dict = None, max_tiles: int = DEFAULT_MAX_TILES,
                   max_concurrency: int = DEFAULT_MAX_CONCURRENCY) -> AerialImage:
    """
    Downloads the aerial imagery inside a bounding box to a georeferenced file
    (world file, ``.aux.xml`` and ``.json`` beside it; see :func:`mirrorworld.aerial.util.save_aerial_image`).

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
    # Bing answers 200 with a placeholder PNG and flags it in a header.
    return get_header(response.headers, "X-VE-Tile-Info") == "no-tile"


def _tile_at(lat: float, lon: float, zoom: int):
    px, py = wgs84_to_pixel(lat, lon, zoom)
    return int(px // TILE_SIZE), int(py // TILE_SIZE)
