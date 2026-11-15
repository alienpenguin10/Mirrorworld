# Mirrorworld addition (not in upstream streetlevel).
"""
ArcGIS REST client for ``ImageServer`` (``exportImage``, which returns data values such as elevations) and
``MapServer`` (``export``, which returns rendered images) endpoints.
"""
from typing import Optional

from aiohttp import ClientSession

from .util import fetch_bytes_async, raise_if_error_document, mosaic_async, epsg_code, make_raster
from ..aerial.util import run_sync
from ..raster import Raster, bbox_to_crs, grid_for_bounds, read_geotiff, read_image

import json


def get_info(url: str) -> dict:
    """
    Fetches a service's description (extent, pixel type, resolution, copyright, ...).

    :param url: Service URL ending in ``/ImageServer`` or ``/MapServer``.
    :return: The JSON description.
    """
    return run_sync(get_info_async, url)


async def get_info_async(url: str, session: ClientSession) -> dict:
    body, _ = await fetch_bytes_async(session, url, {"f": "json"})
    return json.loads(body)


def get_raster(url: str, north: float, west: float, south: float, east: float, resolution: float,
               crs: str = "EPSG:3857", image_format: Optional[str] = None, pixel_type: Optional[str] = None,
               rendering_rule: Optional[dict] = None, extra_params: dict = None, max_size: int = 4000,
               max_concurrency: int = 4) -> Raster:
    """
    Exports a bounding box from an ArcGIS ImageServer or MapServer, in chunks for large areas.

    :param url: Service URL ending in ``/ImageServer`` or ``/MapServer``.
    :param north: Latitude of the top edge.
    :param west: Longitude of the left edge.
    :param south: Latitude of the bottom edge.
    :param east: Longitude of the right edge.
    :param resolution: Pixel size in units of ``crs``.
    :param crs: *(optional)* Output CRS. Defaults to EPSG:3857.
    :param image_format: *(optional)* Defaults to ``tiff`` for ImageServer (values kept; needs rasterio) and
        ``png32`` for MapServer.
    :param pixel_type: *(optional)* ImageServer pixel type, e.g. ``F32``. Defaults to the service's own.
    :param rendering_rule: *(optional)* ImageServer rendering rule, e.g. ``{"rasterFunction": "Hillshade Gray"}``.
    :param extra_params: *(optional)* Further request parameters, e.g. ``{"layers": "show:0"}`` or ``{"time": ...}``.
    :param max_size: *(optional)* Largest chunk side in pixels. Defaults to 4000.
    :param max_concurrency: *(optional)* Maximum number of simultaneous requests. Defaults to 4.
    :return: The raster.
    """
    return run_sync(get_raster_async, url, north, west, south, east, resolution=resolution, crs=crs,
                    image_format=image_format, pixel_type=pixel_type, rendering_rule=rendering_rule,
                    extra_params=extra_params, max_size=max_size, max_concurrency=max_concurrency)


async def get_raster_async(url: str, north: float, west: float, south: float, east: float, session: ClientSession,
                           resolution: float, crs: str = "EPSG:3857", image_format: Optional[str] = None,
                           pixel_type: Optional[str] = None, rendering_rule: Optional[dict] = None,
                           extra_params: dict = None, max_size: int = 4000, max_concurrency: int = 4) -> Raster:
    url = url.rstrip("/")
    image_server = url.lower().endswith("imageserver")
    endpoint = f"{url}/exportImage" if image_server else f"{url}/export"
    image_format = image_format or ("tiff" if image_server else "png32")
    sr = epsg_code(crs)
    transform, width, height = grid_for_bounds(bbox_to_crs(north, west, south, east, crs), resolution)

    async def fetch_chunk(bounds, w, h):
        params = {"bbox": ",".join(str(v) for v in bounds), "bboxSR": sr, "imageSR": sr, "size": f"{w},{h}",
                  "format": image_format, "f": "image"}
        if image_server:
            if pixel_type:
                params["pixelType"] = pixel_type
            if rendering_rule:
                params["renderingRule"] = json.dumps(rendering_rule)
        else:
            params["dpi"] = 96
        params.update(extra_params or {})
        body, content_type = await fetch_bytes_async(session, endpoint, params)
        raise_if_error_document(body, content_type)
        if "tif" in content_type or body[:4] in (b"II*\x00", b"MM\x00*"):
            raster = read_geotiff(body)
            return raster.data, raster.nodata
        return read_image(body), None

    array, nodata = await mosaic_async(transform, width, height, fetch_chunk, max_size, max_concurrency)
    return make_raster(array, nodata, crs, transform, source="ArcGIS", url=url, format=image_format)


def download_raster(url: str, north: float, west: float, south: float, east: float, path: str,
                    resolution: float, **kwargs) -> Raster:
    """
    Same as :func:`get_raster`, then saves the result.

    :param path: Output path (``.tif`` keeps data values).
    :return: The raster.
    """
    raster = get_raster(url, north, west, south, east, resolution, **kwargs)
    raster.save(path)
    return raster
