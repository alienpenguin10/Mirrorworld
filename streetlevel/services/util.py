# Mirrorworld addition (not in upstream streetlevel).
"""Request, chunking and mosaicking helpers shared by the map-service clients."""
import asyncio
import math
from typing import Awaitable, Callable, Optional, Tuple

import numpy as np
from aiohttp import ClientSession, ClientTimeout, ClientError

from ..raster import Raster

HEADERS = {"User-Agent": "streetlevel (Python)"}
FetchChunk = Callable[[Tuple[float, float, float, float], int, int], Awaitable[Tuple[np.ndarray, Optional[float]]]]


STALL_TIMEOUT = 8
"""Seconds without receiving any bytes after which a request is abandoned and retried."""


class ServiceError(RuntimeError):
    """A map service answered with an error message instead of data."""


async def fetch_bytes_async(session: ClientSession, url: str, params: dict = None, retries: int = 6,
                            timeout: float = 120) -> Tuple[bytes, str]:
    """
    GETs a URL, retrying server errors and timeouts, and raises ``ServiceError`` with the server's message
    when it returns an XML/JSON/HTML error instead of data.

    :return: (body, content type).
    """
    last = None
    for attempt in range(retries):
        try:
            # Short connect/read timeouts: some servers (e.g. the Environment Agency's) occasionally stall a
            # request without answering, and retrying quickly beats waiting out the total timeout.
            async with session.get(url, params=params, headers=HEADERS,
                                   timeout=ClientTimeout(total=timeout, sock_connect=10,
                                                         sock_read=STALL_TIMEOUT)) as response:
                body = await response.read()
                content_type = response.headers.get("Content-Type", "")
                if response.status >= 500:
                    last = f"HTTP {response.status}"
                elif response.status != 200:
                    raise ServiceError(f"HTTP {response.status} from {response.url}: {body[:500]!r}")
                else:
                    return body, content_type
        except (asyncio.TimeoutError, ClientError) as e:
            last = repr(e)
        await asyncio.sleep(min(2 ** attempt, 20) if last and last.startswith("HTTP") else 0.5)
    raise ServiceError(f"Request failed after {retries} attempts ({last}): {url}")


def raise_if_error_document(body: bytes, content_type: str, expect_image: bool = True) -> None:
    """Map services often answer errors with status 200 and an XML/JSON document."""
    if expect_image and not content_type.startswith("image/") and "tiff" not in content_type:
        raise ServiceError(f"Expected an image but got {content_type}: {body[:800].decode(errors='replace')}")


async def mosaic_async(transform, width: int, height: int, fetch_chunk: FetchChunk, max_size: int,
                       max_concurrency: int = 4) -> Tuple[np.ndarray, Optional[float]]:
    """
    Fills a pixel grid by requesting it in chunks of at most ``max_size`` x ``max_size`` pixels.

    :param transform: Affine transform of the grid (north-up).
    :param width: Grid width in pixels.
    :param height: Grid height in pixels.
    :param fetch_chunk: Coroutine taking (minx, miny, maxx, maxy), width, height and returning
        (array of shape (bands, height, width), nodata).
    :param max_size: Largest chunk side in pixels.
    :param max_concurrency: *(optional)* Maximum number of simultaneous requests.
    :return: (array, nodata).
    """
    a, _, xoff, _, e, yoff = transform
    semaphore = asyncio.Semaphore(max_concurrency)
    chunks = [(col, row, min(max_size, width - col), min(max_size, height - row))
              for row in range(0, height, max_size) for col in range(0, width, max_size)]

    async def one(col, row, w, h):
        bounds = (xoff + a * col, yoff + e * (row + h), xoff + a * (col + w), yoff + e * row)
        async with semaphore:
            return col, row, await fetch_chunk(bounds, w, h)

    results = await asyncio.gather(*(one(*c) for c in chunks))
    first = results[0][2][0]
    nodata = results[0][2][1]
    fill = nodata if nodata is not None else 0
    out = np.full((first.shape[0], height, width), fill, dtype=first.dtype)
    for col, row, (array, _) in results:
        h, w = min(array.shape[1], height - row), min(array.shape[2], width - col)
        out[:, row:row + h, col:col + w] = array[:, :h, :w]
    return out, nodata


def epsg_code(crs: str) -> int:
    """``EPSG:28992`` -> 28992."""
    from pyproj import CRS
    code = CRS.from_user_input(crs).to_epsg()
    if code is None:
        raise ValueError(f"{crs} has no EPSG code")
    return code


def is_north_first(crs: str) -> bool:
    """Whether the CRS lists northing/latitude first (e.g. EPSG:4326), which WMS 1.3.0 and WMTS respect."""
    from pyproj import CRS
    axes = CRS.from_user_input(crs).axis_info
    return bool(axes) and axes[0].direction.lower() in ("north", "south")


def meters_per_unit(crs: str) -> float:
    from pyproj import CRS
    c = CRS.from_user_input(crs)
    if c.is_geographic:
        return 2 * math.pi * 6378137.0 / 360.0
    return c.axis_info[0].unit_conversion_factor


def make_raster(array, nodata, crs, transform, band_names=None, **metadata) -> Raster:
    return Raster(data=array, crs=crs, transform=transform, nodata=nodata, band_names=band_names,
                  metadata=metadata)
