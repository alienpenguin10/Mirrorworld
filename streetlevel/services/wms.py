# Mirrorworld addition (not in upstream streetlevel).
"""OGC Web Map Service (WMS 1.1.1 and 1.3.0) client."""
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Optional, Sequence, Union

from aiohttp import ClientSession

from .util import fetch_bytes_async, raise_if_error_document, mosaic_async, is_north_first, make_raster
from ..aerial.util import run_sync
from ..raster import Raster, bbox_to_crs, grid_for_bounds, read_geotiff, read_image


@dataclass
class WmsLayer:
    """A layer advertised in WMS capabilities."""

    name: str
    """Layer name to request."""
    title: str
    """Human-readable title."""
    abstract: Optional[str]
    """Description."""
    crs: List[str]
    """Supported coordinate reference systems."""
    bbox_wgs84: Optional[tuple]
    """(north, west, south, east), if advertised."""


def get_layers(url: str, version: str = "1.3.0") -> List[WmsLayer]:
    """
    Lists the named layers of a WMS.

    :param url: Service URL (without request parameters).
    :param version: *(optional)* WMS version. Defaults to 1.3.0.
    :return: A list of WmsLayer objects.
    """
    return run_sync(get_layers_async, url, version=version)


async def get_layers_async(url: str, session: ClientSession, version: str = "1.3.0") -> List[WmsLayer]:
    body, _ = await fetch_bytes_async(session, url, {"service": "WMS", "request": "GetCapabilities",
                                                     "version": version})
    return parse_capabilities(body)


def get_raster(url: str, layers: Union[str, Sequence[str]], north: float, west: float, south: float, east: float,
               resolution: float, crs: str = "EPSG:3857", styles: str = "", image_format: str = "image/png",
               version: str = "1.3.0", transparent: bool = False, extra_params: dict = None,
               max_size: int = 2048, max_concurrency: int = 4) -> Raster:
    """
    Renders a bounding box from a WMS into a georeferenced raster, requesting large areas in chunks.

    :param url: Service URL (without request parameters).
    :param layers: Layer name, or several names to draw on top of each other.
    :param north: Latitude of the top edge.
    :param west: Longitude of the left edge.
    :param south: Latitude of the bottom edge.
    :param east: Longitude of the right edge.
    :param resolution: Pixel size in units of ``crs`` (meters for projected systems).
    :param crs: *(optional)* Output CRS; must be one the layer supports. Defaults to EPSG:3857.
    :param styles: *(optional)* Style names. Defaults to the default style.
    :param image_format: *(optional)* ``image/png``, ``image/jpeg`` or, where supported, ``image/tiff``
        (needs rasterio; keeps values such as elevations). Defaults to ``image/png``.
    :param version: *(optional)* ``1.3.0`` or ``1.1.1``. Defaults to 1.3.0.
    :param transparent: *(optional)* Request a transparent background. Defaults to False.
    :param extra_params: *(optional)* Vendor parameters, e.g. ``{"TIME": "2024-06-01"}``.
    :param max_size: *(optional)* Largest image side per request; many servers cap this. Defaults to 2048.
    :param max_concurrency: *(optional)* Maximum number of simultaneous requests. Defaults to 4.
    :return: The raster.
    """
    return run_sync(get_raster_async, url, layers, north, west, south, east, resolution=resolution, crs=crs,
                    styles=styles, image_format=image_format, version=version, transparent=transparent,
                    extra_params=extra_params, max_size=max_size, max_concurrency=max_concurrency)


async def get_raster_async(url: str, layers: Union[str, Sequence[str]], north: float, west: float, south: float,
                           east: float, session: ClientSession, resolution: float, crs: str = "EPSG:3857",
                           styles: str = "", image_format: str = "image/png", version: str = "1.3.0",
                           transparent: bool = False, extra_params: dict = None, max_size: int = 2048,
                           max_concurrency: int = 4) -> Raster:
    layer_param = layers if isinstance(layers, str) else ",".join(layers)
    transform, width, height = grid_for_bounds(bbox_to_crs(north, west, south, east, crs), resolution)

    async def fetch_chunk(bounds, w, h):
        params = build_getmap_params(layer_param, bounds, w, h, crs, styles, image_format, version, transparent)
        params.update(extra_params or {})
        body, content_type = await fetch_bytes_async(session, url, params)
        raise_if_error_document(body, content_type)
        if "tiff" in content_type:
            raster = read_geotiff(body)
            return raster.data, raster.nodata
        return read_image(body), None

    array, nodata = await mosaic_async(transform, width, height, fetch_chunk, max_size, max_concurrency)
    return make_raster(array, nodata, crs, transform, source="WMS", url=url, layers=layer_param,
                       styles=styles, format=image_format)


def download_raster(url: str, layers: Union[str, Sequence[str]], north: float, west: float, south: float,
                    east: float, path: str, resolution: float, crs: str = "EPSG:3857", **kwargs) -> Raster:
    """
    Same as :func:`get_raster`, then saves the result (see :meth:`streetlevel.raster.Raster.save`).

    :param path: Output path (``.tif`` for GeoTIFF, ``.png``/``.jpg`` for an image with a world file).
    :return: The raster.
    """
    raster = get_raster(url, layers, north, west, south, east, resolution, crs, **kwargs)
    raster.save(path)
    return raster


def build_getmap_params(layers: str, bounds, width: int, height: int, crs: str, styles: str = "",
                        image_format: str = "image/png", version: str = "1.3.0",
                        transparent: bool = False) -> dict:
    minx, miny, maxx, maxy = bounds
    if version == "1.3.0" and is_north_first(crs):
        bbox = f"{miny},{minx},{maxy},{maxx}"
    else:
        bbox = f"{minx},{miny},{maxx},{maxy}"
    return {"service": "WMS", "request": "GetMap", "version": version, "layers": layers, "styles": styles,
            ("crs" if version == "1.3.0" else "srs"): crs, "bbox": bbox, "width": width, "height": height,
            "format": image_format, "transparent": "true" if transparent else "false"}


def parse_capabilities(xml: bytes) -> List[WmsLayer]:
    root = ET.fromstring(xml)
    layers = []
    for element in root.iter():
        if _local(element.tag) != "Layer":
            continue
        name = _child_text(element, "Name")
        if not name:
            continue
        crs = [c.text for c in element if _local(c.tag) in ("CRS", "SRS") and c.text]
        bbox = None
        for child in element:
            if _local(child.tag) == "EX_GeographicBoundingBox":
                values = {_local(c.tag): float(c.text) for c in child}
                bbox = (values["northBoundLatitude"], values["westBoundLongitude"],
                        values["southBoundLatitude"], values["eastBoundLongitude"])
            elif _local(child.tag) == "LatLonBoundingBox":
                bbox = (float(child.get("maxy")), float(child.get("minx")),
                        float(child.get("miny")), float(child.get("maxx")))
        layers.append(WmsLayer(name=name, title=_child_text(element, "Title") or name,
                               abstract=_child_text(element, "Abstract"), crs=crs, bbox_wgs84=bbox))
    return layers


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child_text(element, name: str) -> Optional[str]:
    for child in element:
        if _local(child.tag) == name:
            return (child.text or "").strip() or None
    return None
