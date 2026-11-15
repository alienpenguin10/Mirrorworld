# SURVAI: added module (not upstream).
"""Tile math, downloading, stitching and saving shared by all aerial providers."""
import asyncio
import json
import math
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Set, Tuple

from PIL import Image
from aiohttp import ClientSession

from .dataclasses import AerialImage

TILE_SIZE = 256
EARTH_CIRCUMFERENCE = 2 * math.pi * 6378137.0
MAX_LATITUDE = 85.05112878
DEFAULT_MAX_TILES = 20000
DEFAULT_MAX_CONCURRENCY = 8
HEADERS = {"User-Agent": "Mozilla/5.0"}


@dataclass
class TileResponse:
    """The raw response for one tile."""

    x: int
    """X coordinate of the tile."""
    y: int
    """Y coordinate of the tile."""
    status: int
    """HTTP status code."""
    headers: Dict[str, str]
    """Response headers."""
    data: bytes
    """Response body."""


def ground_resolution(lat: float, zoom: int) -> float:
    """
    Calculates the ground resolution of a Web Mercator tile pyramid.

    :param lat: Latitude.
    :param zoom: Zoom level.
    :return: Meters per pixel on the ground.
    """
    return math.cos(math.radians(lat)) * EARTH_CIRCUMFERENCE / (TILE_SIZE * 2 ** zoom)


def zoom_for_resolution(lat: float, meters_per_pixel: float) -> int:
    """
    Finds the zoom level whose ground resolution is closest (on a log scale) to the requested one.

    :param lat: Latitude.
    :param meters_per_pixel: Target ground resolution.
    :return: The zoom level, e.g. 20 for 0.10 m at 47.6° N.
    """
    return round(math.log2(math.cos(math.radians(lat)) * EARTH_CIRCUMFERENCE / (TILE_SIZE * meters_per_pixel)))


def wgs84_to_pixel(lat: float, lon: float, zoom: int) -> Tuple[float, float]:
    """
    Converts WGS84 coordinates to global pixel coordinates of a Web Mercator tile pyramid.

    :param lat: Latitude.
    :param lon: Longitude.
    :param zoom: Zoom level.
    :return: The X and Y pixel coordinates.
    """
    lat = min(max(lat, -MAX_LATITUDE), MAX_LATITUDE)
    size = TILE_SIZE * 2 ** zoom
    x = (lon + 180.0) / 360.0 * size
    s = math.sin(math.radians(lat))
    y = (0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * size
    return x, y


def pixel_to_wgs84(x: float, y: float, zoom: int) -> Tuple[float, float]:
    """
    Converts global pixel coordinates of a Web Mercator tile pyramid to WGS84 coordinates.

    :param x: X pixel coordinate.
    :param y: Y pixel coordinate.
    :param zoom: Zoom level.
    :return: Latitude and longitude.
    """
    size = TILE_SIZE * 2 ** zoom
    lon = x / size * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / size))))
    return lat, lon


def bbox_to_pixels(north: float, west: float, south: float, east: float,
                   zoom: int) -> Tuple[int, int, int, int]:
    """
    Converts a bounding box to the global pixel window that covers it.

    :return: Left, top, right, bottom (right/bottom exclusive).
    """
    if north <= south or east <= west:
        raise ValueError("Expected north > south and east > west")
    left, top = wgs84_to_pixel(north, west, zoom)
    right, bottom = wgs84_to_pixel(south, east, zoom)
    return math.floor(left), math.floor(top), math.ceil(right), math.ceil(bottom)


def tiles_in_pixel_window(left: int, top: int, right: int, bottom: int) -> List[Tuple[int, int]]:
    """
    Lists the tiles that intersect a global pixel window, row by row.

    :return: X/Y tile coordinates.
    """
    return [(x, y)
            for y in range(top // TILE_SIZE, (bottom - 1) // TILE_SIZE + 1)
            for x in range(left // TILE_SIZE, (right - 1) // TILE_SIZE + 1)]


async def download_tiles_async(tiles: Iterable[Tuple[int, int]], build_tile_url: Callable[[int, int], str],
                               session: ClientSession, max_concurrency: int = DEFAULT_MAX_CONCURRENCY,
                               headers: dict = None, retries: int = 4) -> List[TileResponse]:
    """
    Downloads tiles and keeps each response's status and headers, since providers signal missing imagery
    differently (status codes, headers or placeholder images).

    Server errors and connection failures are retried; client errors are returned as they are.

    :param tiles: X/Y tile coordinates.
    :param build_tile_url: Function returning the URL of tile (x, y).
    :param session: A ``ClientSession``.
    :param max_concurrency: *(optional)* Maximum number of simultaneous requests. Defaults to 8.
    :param headers: *(optional)* Request headers. Defaults to a browser user agent.
    :param retries: *(optional)* Number of attempts per tile. Defaults to 4.
    :return: One ``TileResponse`` per tile, in input order.
    """
    headers = headers if headers is not None else HEADERS
    semaphore = asyncio.Semaphore(max_concurrency)

    async def download_one(x: int, y: int) -> TileResponse:
        url = build_tile_url(x, y)
        async with semaphore:
            for attempt in range(retries):
                try:
                    async with session.get(url, headers=headers) as response:
                        if response.status < 500:
                            return TileResponse(x, y, response.status, dict(response.headers),
                                                await response.read())
                except (OSError, asyncio.TimeoutError):
                    if attempt == retries - 1:
                        raise
                await asyncio.sleep(2 ** attempt)
        raise RuntimeError(f"Tile request failed after {retries} attempts: {url}")

    return await asyncio.gather(*(download_one(x, y) for x, y in tiles))


async def get_tiled_image_async(north: float, west: float, south: float, east: float, zoom: int,
                                provider: str,
                                build_tile_url: Callable[[int, int], str],
                                is_missing: Callable[[TileResponse], bool],
                                session: ClientSession,
                                skip_tiles: Optional[Set[Tuple[int, int]]] = None,
                                metadata_headers: Iterable[str] = (),
                                max_tiles: int = DEFAULT_MAX_TILES,
                                max_concurrency: int = DEFAULT_MAX_CONCURRENCY) -> AerialImage:
    """
    Downloads the tiles covering a bounding box and stitches them into one georeferenced image.

    :param north: Latitude of the top edge.
    :param west: Longitude of the left edge.
    :param south: Latitude of the bottom edge.
    :param east: Longitude of the right edge.
    :param zoom: Zoom level.
    :param provider: Provider name stored in the result.
    :param build_tile_url: Function returning the URL of tile (x, y) at this zoom level.
    :param is_missing: Function deciding from a response whether the provider has no imagery for that tile.
    :param session: A ``ClientSession``.
    :param skip_tiles: *(optional)* Tiles already known to be missing; they are not requested.
    :param metadata_headers: *(optional)* Response headers whose distinct values are collected into
        ``AerialImage.metadata``.
    :param max_tiles: *(optional)* Refuse requests covering more tiles than this. Defaults to 20000.
    :param max_concurrency: *(optional)* Maximum number of simultaneous requests. Defaults to 8.
    :return: The stitched image.
    """
    left, top, right, bottom = bbox_to_pixels(north, west, south, east, zoom)
    tiles = tiles_in_pixel_window(left, top, right, bottom)
    if len(tiles) > max_tiles:
        raise ValueError(f"{len(tiles)} tiles requested, more than max_tiles={max_tiles}; "
                         f"split the area or raise max_tiles")

    skip_tiles = skip_tiles or set()
    responses = await download_tiles_async([t for t in tiles if t not in skip_tiles], build_tile_url,
                                           session, max_concurrency)

    tile_x0, tile_y0 = tiles[0]
    image = Image.new("RGB", (right - left, bottom - top))
    missing = sorted(skip_tiles.intersection(tiles))
    collected: Dict[str, Set[str]] = {name: set() for name in metadata_headers}
    for response in responses:
        if is_missing(response):
            missing.append((response.x, response.y))
            continue
        if response.status != 200:
            raise RuntimeError(f"Tile ({response.x}, {response.y}) returned HTTP {response.status}")
        tile = Image.open(BytesIO(response.data)).convert("RGB")
        image.paste(tile, (response.x * TILE_SIZE - left, response.y * TILE_SIZE - top))
        for name in collected:
            value = get_header(response.headers, name)
            if value:
                collected[name].add(value)

    north_edge, west_edge = pixel_to_wgs84(left, top, zoom)
    south_edge, east_edge = pixel_to_wgs84(right, bottom, zoom)
    mercator_resolution = EARTH_CIRCUMFERENCE / (TILE_SIZE * 2 ** zoom)
    return AerialImage(
        image=image,
        provider=provider,
        zoom=zoom,
        north=north_edge, west=west_edge, south=south_edge, east=east_edge,
        origin_x=left * mercator_resolution - EARTH_CIRCUMFERENCE / 2,
        origin_y=EARTH_CIRCUMFERENCE / 2 - top * mercator_resolution,
        mercator_resolution=mercator_resolution,
        ground_resolution=ground_resolution((north_edge + south_edge) / 2, zoom),
        tile_count=len(tiles),
        missing_tiles=sorted(missing),
        metadata={name: sorted(values) for name, values in collected.items()},
    )


def run_sync(coroutine_function: Callable, *args, **kwargs):
    """
    Runs an async function that takes a ``session`` keyword argument with a temporary ``ClientSession``.
    Used to implement the sync variants of the provider functions.
    """
    async def run():
        async with ClientSession() as session:
            return await coroutine_function(*args, session=session, **kwargs)
    return asyncio.run(run())


def save_aerial_image(aerial: AerialImage, path: str, pil_args: dict = None) -> None:
    """
    Saves an aerial image with its georeferencing.

    Next to the image, this writes a world file (``.jgw``, ``.pgw``, ``.tfw`` or ``.wld``) in EPSG:3857 meters,
    a GDAL ``.aux.xml`` sidecar declaring the CRS so that GDAL, rasterio and QGIS place the image correctly,
    and a ``.json`` file with the remaining metadata.

    :param aerial: The image.
    :param path: Output path.
    :param pil_args: *(optional)* Additional arguments for PIL's
        `Image.save <https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.save>`_
        method, e.g. ``{"quality":100}``. Defaults to ``{"quality": 95}`` for JPEG and ``{}`` otherwise.
    """
    out = Path(path)
    suffix = out.suffix.lower()
    if pil_args is None:
        pil_args = {"quality": 95} if suffix in (".jpg", ".jpeg") else {}
    out.parent.mkdir(parents=True, exist_ok=True)
    aerial.image.save(out, **pil_args)

    world_suffix = {".jpg": ".jgw", ".jpeg": ".jgw", ".png": ".pgw", ".tif": ".tfw", ".tiff": ".tfw"}
    res = aerial.mercator_resolution
    # World files reference the center of the top left pixel.
    out.with_suffix(world_suffix.get(suffix, ".wld")).write_text(
        f"{res}\n0.0\n0.0\n{-res}\n{aerial.origin_x + res / 2}\n{aerial.origin_y - res / 2}\n")
    Path(str(out) + ".aux.xml").write_text("<PAMDataset><SRS>EPSG:3857</SRS></PAMDataset>\n")

    metadata = {
        "provider": aerial.provider,
        "crs": "EPSG:3857",
        "zoom": aerial.zoom,
        "bbox_wgs84": {"north": aerial.north, "west": aerial.west, "south": aerial.south, "east": aerial.east},
        "ground_resolution_m": aerial.ground_resolution,
        "mercator_resolution_m": aerial.mercator_resolution,
        "size_px": list(aerial.image.size),
        "tile_count": aerial.tile_count,
        "missing_tiles": aerial.missing_tiles,
        "metadata": aerial.metadata,
    }
    out.with_suffix(".json").write_text(json.dumps(metadata, indent=2))


def get_header(headers: Dict[str, str], name: str) -> Optional[str]:
    name = name.lower()
    for key, value in headers.items():
        if key.lower() == name:
            return value
    return None


def get_tile_response(url: str, x: int, y: int, session=None, headers: dict = None) -> TileResponse:
    """
    Fetches one tile using requests and keeps its status and headers.

    :param url: The tile URL.
    :param x: X coordinate of the tile.
    :param y: Y coordinate of the tile.
    :param session: *(optional)* A requests session.
    :param headers: *(optional)* Request headers. Defaults to a browser user agent.
    """
    import requests
    requester = session if session else requests
    response = requester.get(url, headers=headers if headers is not None else HEADERS, timeout=60)
    return TileResponse(x, y, response.status_code, dict(response.headers), response.content)


async def get_tile_response_async(url: str, x: int, y: int, session: ClientSession,
                                  headers: dict = None) -> TileResponse:
    """
    Fetches one tile using aiohttp and keeps its status and headers.

    :param url: The tile URL.
    :param x: X coordinate of the tile.
    :param y: Y coordinate of the tile.
    :param session: A ``ClientSession``.
    :param headers: *(optional)* Request headers. Defaults to a browser user agent.
    """
    async with session.get(url, headers=headers if headers is not None else HEADERS) as response:
        return TileResponse(x, y, response.status, dict(response.headers), await response.read())


def tile_to_image(response: TileResponse) -> Image.Image:
    """Decodes a tile response."""
    if response.status != 200:
        raise RuntimeError(f"Tile ({response.x}, {response.y}) returned HTTP {response.status}")
    return Image.open(BytesIO(response.data)).convert("RGB")
