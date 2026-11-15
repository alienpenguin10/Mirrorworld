# Mirrorworld addition (not in upstream streetlevel).
"""OGC Web Map Tile Service (WMTS 1.0.0) client for tile matrix sets in projected coordinate systems."""
import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np
from aiohttp import ClientSession

from .util import fetch_bytes_async, raise_if_error_document, is_north_first, meters_per_unit, make_raster, \
    ServiceError
from ..aerial.util import run_sync
from ..raster import Raster, bbox_to_crs, read_image

import asyncio


@dataclass
class TileMatrix:
    """One zoom level of a tile matrix set."""

    identifier: str
    scale_denominator: float
    top_left: tuple
    """Top left corner as (x, y) in CRS coordinates."""
    tile_width: int
    tile_height: int
    matrix_width: int
    matrix_height: int
    resolution: float = 0.0
    """Pixel size in CRS units."""


@dataclass
class TileMatrixSet:
    identifier: str
    crs: str
    matrices: List[TileMatrix]


@dataclass
class WmtsLayer:
    """A layer advertised in WMTS capabilities."""

    identifier: str
    title: str
    formats: List[str]
    styles: List[str]
    tile_matrix_sets: List[str]
    resource_urls: Dict[str, str] = field(default_factory=dict)
    """URL templates by image format (REST encoding)."""


@dataclass
class WmtsCapabilities:
    layers: Dict[str, WmtsLayer]
    tile_matrix_sets: Dict[str, TileMatrixSet]
    get_tile_url: Optional[str] = None
    """Base URL for key-value-pair GetTile requests, if offered."""


def get_capabilities(url: str) -> WmtsCapabilities:
    """
    Reads the layers and tile matrix sets of a WMTS.

    :param url: Capabilities URL, or the service URL to which ``?service=WMTS&request=GetCapabilities`` is added.
    :return: The parsed capabilities.
    """
    return run_sync(get_capabilities_async, url)


async def get_capabilities_async(url: str, session: ClientSession) -> WmtsCapabilities:
    params = None if "request=getcapabilities" in url.lower() or url.lower().endswith(".xml") else \
        {"service": "WMTS", "request": "GetCapabilities"}
    body, _ = await fetch_bytes_async(session, url, params)
    return parse_capabilities(body)


def get_raster(url: str, layer: str, north: float, west: float, south: float, east: float,
               resolution: Optional[float] = None, tile_matrix_set: Optional[str] = None,
               crs: Optional[str] = None, style: Optional[str] = None, image_format: Optional[str] = None,
               max_tiles: int = 10000, max_concurrency: int = 8) -> Raster:
    """
    Downloads and stitches the WMTS tiles covering a bounding box, cropped to the box.

    The raster keeps the tile matrix's native pixel grid (no resampling), so its resolution is that of the chosen
    matrix: the coarsest one at least as fine as ``resolution``, or the finest one.

    :param url: Capabilities URL or service URL.
    :param layer: Layer identifier.
    :param north: Latitude of the top edge.
    :param west: Longitude of the left edge.
    :param south: Latitude of the bottom edge.
    :param east: Longitude of the right edge.
    :param resolution: *(optional)* Wanted pixel size in CRS units. Defaults to the finest level.
    :param tile_matrix_set: *(optional)* Tile matrix set identifier. Defaults to one in ``crs``, else the first
        projected one the layer offers.
    :param crs: *(optional)* Preferred CRS when choosing the tile matrix set, e.g. ``EPSG:28992``.
    :param style: *(optional)* Style identifier. Defaults to the layer's first style.
    :param image_format: *(optional)* Tile format. Defaults to the layer's first format.
    :param max_tiles: *(optional)* Refuse requests covering more tiles than this. Defaults to 10000.
    :param max_concurrency: *(optional)* Maximum number of simultaneous requests. Defaults to 8.
    :return: The raster.
    """
    return run_sync(get_raster_async, url, layer, north, west, south, east, resolution=resolution,
                    tile_matrix_set=tile_matrix_set, crs=crs, style=style, image_format=image_format,
                    max_tiles=max_tiles, max_concurrency=max_concurrency)


async def get_raster_async(url: str, layer: str, north: float, west: float, south: float, east: float,
                           session: ClientSession, resolution: Optional[float] = None,
                           tile_matrix_set: Optional[str] = None, crs: Optional[str] = None,
                           style: Optional[str] = None, image_format: Optional[str] = None,
                           max_tiles: int = 10000, max_concurrency: int = 8) -> Raster:
    caps = await get_capabilities_async(url, session)
    if layer not in caps.layers:
        raise ValueError(f"Unknown layer {layer!r}; available: {sorted(caps.layers)}")
    lyr = caps.layers[layer]
    tms = choose_tile_matrix_set(caps, lyr, tile_matrix_set, crs)
    matrix = choose_matrix(tms, resolution)
    image_format = image_format or (lyr.formats[0] if lyr.formats else "image/png")
    style = style or (lyr.styles[0] if lyr.styles else "default")

    minx, miny, maxx, maxy = bbox_to_crs(north, west, south, east, tms.crs)
    span_x, span_y = matrix.tile_width * matrix.resolution, matrix.tile_height * matrix.resolution
    x0, y0 = matrix.top_left
    col0, col1 = math.floor((minx - x0) / span_x), math.floor((maxx - x0) / span_x)
    row0, row1 = math.floor((y0 - maxy) / span_y), math.floor((y0 - miny) / span_y)
    col0, row0 = max(col0, 0), max(row0, 0)
    col1, row1 = min(col1, matrix.matrix_width - 1), min(row1, matrix.matrix_height - 1)
    count = (col1 - col0 + 1) * (row1 - row0 + 1)
    if count <= 0:
        raise ValueError("The bounding box is outside the tile matrix")
    if count > max_tiles:
        raise ValueError(f"{count} tiles requested, more than max_tiles={max_tiles}")

    template = lyr.resource_urls.get(image_format)
    semaphore = asyncio.Semaphore(max_concurrency)

    async def fetch(col, row):
        if template:
            tile_url = (template.replace("{TileMatrixSet}", tms.identifier).replace("{TileMatrix}", matrix.identifier)
                        .replace("{TileRow}", str(row)).replace("{TileCol}", str(col)).replace("{Style}", style)
                        .replace("{style}", style))
            params = None
        elif caps.get_tile_url:
            tile_url = caps.get_tile_url
            params = {"service": "WMTS", "request": "GetTile", "version": "1.0.0", "layer": layer, "style": style,
                      "format": image_format, "tileMatrixSet": tms.identifier, "tileMatrix": matrix.identifier,
                      "tileRow": row, "tileCol": col}
        else:
            raise ServiceError("The service advertises neither REST templates nor KVP GetTile")
        async with semaphore:
            try:
                body, content_type = await fetch_bytes_async(session, tile_url, params)
            except ServiceError:
                return col, row, None
        if not content_type.startswith("image/"):
            return col, row, None
        return col, row, read_image(body)

    results = await asyncio.gather(*(fetch(c, r) for r in range(row0, row1 + 1) for c in range(col0, col1 + 1)))
    bands = next((a.shape[0] for _, _, a in results if a is not None), 3)
    full = np.zeros((bands, (row1 - row0 + 1) * matrix.tile_height, (col1 - col0 + 1) * matrix.tile_width),
                    dtype=np.uint8)
    missing = []
    for col, row, array in results:
        if array is None:
            missing.append((col, row))
            continue
        if array.shape[0] != bands:
            array = np.repeat(array[:1], bands, axis=0) if array.shape[0] == 1 else array[:bands]
        oy, ox = (row - row0) * matrix.tile_height, (col - col0) * matrix.tile_width
        full[:, oy:oy + array.shape[1], ox:ox + array.shape[2]] = array

    # Crop to the requested box on the native grid.
    grid_x0 = x0 + col0 * span_x
    grid_y0 = y0 - row0 * span_y
    left = max(0, math.floor((minx - grid_x0) / matrix.resolution))
    top = max(0, math.floor((grid_y0 - maxy) / matrix.resolution))
    right = min(full.shape[2], math.ceil((maxx - grid_x0) / matrix.resolution))
    bottom = min(full.shape[1], math.ceil((grid_y0 - miny) / matrix.resolution))
    array = full[:, top:bottom, left:right]
    transform = (matrix.resolution, 0.0, grid_x0 + left * matrix.resolution, 0.0, -matrix.resolution,
                 grid_y0 - top * matrix.resolution)
    return make_raster(array, None, tms.crs, transform, source="WMTS", url=url, layer=layer,
                       tile_matrix_set=tms.identifier, tile_matrix=matrix.identifier, missing_tiles=missing)


def download_raster(url: str, layer: str, north: float, west: float, south: float, east: float, path: str,
                    **kwargs) -> Raster:
    """
    Same as :func:`get_raster`, then saves the result (see :meth:`mirrorworld.raster.Raster.save`).

    :param path: Output path.
    :return: The raster.
    """
    raster = get_raster(url, layer, north, west, south, east, **kwargs)
    raster.save(path)
    return raster


def choose_tile_matrix_set(caps: WmtsCapabilities, layer: WmtsLayer, identifier: Optional[str] = None,
                           crs: Optional[str] = None) -> TileMatrixSet:
    candidates = [caps.tile_matrix_sets[t] for t in layer.tile_matrix_sets if t in caps.tile_matrix_sets]
    if identifier:
        for tms in candidates:
            if tms.identifier == identifier:
                return tms
        raise ValueError(f"Layer {layer.identifier!r} has no tile matrix set {identifier!r}")
    if crs:
        for tms in candidates:
            if tms.crs == crs:
                return tms
    for tms in candidates:
        if not is_north_first(tms.crs):
            return tms
    raise ValueError("No projected tile matrix set; pass tile_matrix_set explicitly")


def choose_matrix(tms: TileMatrixSet, resolution: Optional[float]) -> TileMatrix:
    by_res = sorted(tms.matrices, key=lambda m: m.resolution)  # finest first
    if resolution is None:
        return by_res[0]
    fine_enough = [m for m in by_res if m.resolution <= resolution * 1.001]
    return fine_enough[-1] if fine_enough else by_res[0]


def parse_capabilities(xml: bytes) -> WmtsCapabilities:
    root = ET.fromstring(xml)
    contents = _find(root, "Contents")
    tile_matrix_sets = {}
    for tms_el in _children(contents, "TileMatrixSet"):
        identifier = _text(tms_el, "Identifier")
        crs = _normalize_crs(_text(tms_el, "SupportedCRS"))
        north_first = is_north_first(crs)
        mpu = meters_per_unit(crs)
        matrices = []
        for m in _children(tms_el, "TileMatrix"):
            a, b = (float(v) for v in _text(m, "TopLeftCorner").split())
            matrix = TileMatrix(
                identifier=_text(m, "Identifier"), scale_denominator=float(_text(m, "ScaleDenominator")),
                top_left=(b, a) if north_first else (a, b), tile_width=int(_text(m, "TileWidth")),
                tile_height=int(_text(m, "TileHeight")), matrix_width=int(_text(m, "MatrixWidth")),
                matrix_height=int(_text(m, "MatrixHeight")))
            # The standard's 0.28 mm "standardized rendering pixel size".
            matrix.resolution = matrix.scale_denominator * 0.00028 / mpu
            matrices.append(matrix)
        tile_matrix_sets[identifier] = TileMatrixSet(identifier, crs, matrices)

    layers = {}
    for lyr in _children(contents, "Layer"):
        identifier = _text(lyr, "Identifier")
        styles = [_text(s, "Identifier") for s in _children(lyr, "Style")]
        links = [_text(link, "TileMatrixSet") for link in _children(lyr, "TileMatrixSetLink")]
        resource_urls = {r.get("format"): r.get("template") for r in _children(lyr, "ResourceURL")
                         if r.get("resourceType", "tile") == "tile"}
        layers[identifier] = WmtsLayer(identifier=identifier, title=_text(lyr, "Title") or identifier,
                                       formats=[f.text for f in _children(lyr, "Format")], styles=styles,
                                       tile_matrix_sets=links, resource_urls=resource_urls)

    get_tile_url = None
    for op in root.iter():
        if _local(op.tag) == "Operation" and op.get("name") == "GetTile":
            for get in op.iter():
                if _local(get.tag) == "Get":
                    href = get.get("{http://www.w3.org/1999/xlink}href")
                    if href:
                        get_tile_url = href.split("?")[0]
                        break
    return WmtsCapabilities(layers=layers, tile_matrix_sets=tile_matrix_sets, get_tile_url=get_tile_url)


def _normalize_crs(value: str) -> str:
    match = re.search(r"EPSG(?::|/0/|::|:\d*:)(\d+)", value or "")
    if match:
        return f"EPSG:{match.group(1)}"
    if value and "CRS84" in value:
        return "OGC:CRS84"
    return value


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _find(element, name):
    for child in element.iter():
        if _local(child.tag) == name:
            return child
    raise ServiceError(f"No {name} element in capabilities")


def _children(element, name):
    return [c for c in element if _local(c.tag) == name]


def _text(element, name) -> Optional[str]:
    for child in element:
        if _local(child.tag) == name:
            return (child.text or "").strip()
    return None
