# Mirrorworld addition (not in upstream streetlevel).
"""
Generic STAC client: search a STAC API and read assets of the found items for a bounding box onto one grid.

Searching is plain HTTP (sync and async). Reading uses GDAL through rasterio and is sync only.
"""
import time
from datetime import datetime
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Union
from urllib.parse import urlparse

import numpy as np
import requests
from aiohttp import ClientSession

from .scene import Scene
from ..raster import Raster, bbox_to_crs, grid_for_bounds, require_rasterio

EARTH_SEARCH = "https://earth-search.aws.element84.com/v1"
PLANETARY_COMPUTER = "https://planetarycomputer.microsoft.com/api/stac/v1"
HEADERS = {"User-Agent": "streetlevel (Python)"}
GDAL_ENV = {"GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR", "GDAL_HTTP_MAX_RETRY": "5",
            "GDAL_HTTP_RETRY_DELAY": "1", "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": ".tif,.TIF,.tiff,.TIFF",
            "GDAL_HTTP_MULTIRANGE": "YES", "GDAL_HTTP_MERGE_CONSECUTIVE_RANGES": "YES"}


def search(endpoint: str, collections: Union[str, Sequence[str]], north: float, west: float, south: float,
           east: float, start: Union[str, datetime, None] = None, end: Union[str, datetime, None] = None,
           max_cloud_cover: Optional[float] = None, query: Optional[dict] = None, limit: int = 100,
           session: requests.Session = None) -> List[Scene]:
    """
    Searches a STAC API for items intersecting a bounding box, newest first.

    :param endpoint: STAC API root, e.g. :data:`EARTH_SEARCH` or :data:`PLANETARY_COMPUTER`.
    :param collections: Collection ID(s).
    :param north: Latitude of the top edge.
    :param west: Longitude of the left edge.
    :param south: Latitude of the bottom edge.
    :param east: Longitude of the right edge.
    :param start: *(optional)* Earliest acquisition, e.g. ``"2024-06-01"``.
    :param end: *(optional)* Latest acquisition.
    :param max_cloud_cover: *(optional)* Maximum ``eo:cloud_cover`` in percent.
    :param query: *(optional)* Further STAC query conditions, e.g. ``{"sat:orbit_state": {"eq": "ascending"}}``.
    :param limit: *(optional)* Maximum number of items. Defaults to 100.
    :param session: *(optional)* A requests session.
    :return: A list of Scene objects.
    """
    body = build_search_body(collections, north, west, south, east, start, end, max_cloud_cover, query, limit)
    requester = session if session else requests
    scenes, url, method = [], f"{endpoint.rstrip('/')}/search", "POST"
    while url and len(scenes) < limit:
        if method == "POST":
            response = requester.post(url, json=body, headers=HEADERS, timeout=120)
        else:
            response = requester.get(url, headers=HEADERS, timeout=120)
        response.raise_for_status()
        page = response.json()
        scenes += [parse_item(item, endpoint) for item in page.get("features", [])]
        url, body, method = _next_page(page, body)
    return _sorted(scenes)[:limit]


async def search_async(endpoint: str, collections: Union[str, Sequence[str]], north: float, west: float,
                       south: float, east: float, session: ClientSession, start: Union[str, datetime, None] = None,
                       end: Union[str, datetime, None] = None, max_cloud_cover: Optional[float] = None,
                       query: Optional[dict] = None, limit: int = 100) -> List[Scene]:
    body = build_search_body(collections, north, west, south, east, start, end, max_cloud_cover, query, limit)
    scenes, url, method = [], f"{endpoint.rstrip('/')}/search", "POST"
    while url and len(scenes) < limit:
        request = session.post(url, json=body, headers=HEADERS) if method == "POST" else \
            session.get(url, headers=HEADERS)
        async with request as response:
            response.raise_for_status()
            page = await response.json(content_type=None)
        scenes += [parse_item(item, endpoint) for item in page.get("features", [])]
        url, body, method = _next_page(page, body)
    return _sorted(scenes)[:limit]


def read(scenes: Union[Scene, Sequence[Scene]], assets: Sequence[str], north: float, west: float, south: float,
         east: float, resolution: Optional[float] = None, crs: Optional[str] = None, resampling: str = "nearest",
         dtype: Optional[str] = None) -> Raster:
    """
    Reads assets of one or more items for a bounding box onto a common grid.

    With several items (e.g. adjacent tiles of one pass, or a time series to composite), the first item with
    data at a pixel wins, so pass them in order of preference.

    :param scenes: A Scene or a list of Scenes.
    :param assets: Asset names, e.g. ``["red", "green", "blue", "nir"]``. Multi-band assets (e.g. NAIP's
        ``image``) contribute all their bands.
    :param north: Latitude of the top edge.
    :param west: Longitude of the left edge.
    :param south: Latitude of the bottom edge.
    :param east: Longitude of the right edge.
    :param resolution: *(optional)* Pixel size in units of ``crs``. Defaults to the first asset's native size.
    :param crs: *(optional)* Output CRS. Defaults to the first asset's native CRS.
    :param resampling: *(optional)* ``nearest``, ``bilinear``, ``cubic``, ``average``, ... Defaults to nearest.
    :param dtype: *(optional)* Output data type. Defaults to the first asset's.
    :return: A Raster with one band per asset band; ``metadata`` lists the item IDs, dates and scale/offset
        of each band where the catalogue gives them.
    """
    rasterio = require_rasterio()
    from rasterio.enums import Resampling
    from rasterio.transform import Affine
    from rasterio.vrt import WarpedVRT

    scenes = [scenes] if isinstance(scenes, Scene) else list(scenes)
    if not scenes:
        raise ValueError("No scenes to read")
    resampling_method = Resampling[resampling]
    with rasterio.Env(**GDAL_ENV):
        first_href = sign_href(scenes[0], _asset(scenes[0], assets[0])["href"])
        with rasterio.open(first_href) as src:
            crs = crs or src.crs.to_string()
            if resolution is None:
                if crs == src.crs.to_string():
                    resolution = abs(src.transform.a)
                else:
                    raise ValueError("Pass resolution when reprojecting")
            dtype = dtype or src.dtypes[0]
        transform, width, height = grid_for_bounds(bbox_to_crs(north, west, south, east, crs), resolution)

        bands, names, band_info = [], [], []
        for asset_name in assets:
            stack, filled, nodata_value = None, None, None
            for scene in scenes:
                asset = scene.assets.get(asset_name)
                if asset is None:
                    continue
                href = sign_href(scene, asset["href"])
                with rasterio.open(href) as src:
                    nodata_value = src.nodata if src.nodata is not None else nodata_value
                    with WarpedVRT(src, crs=crs, transform=Affine(*transform), width=width, height=height,
                                   resampling=resampling_method, src_nodata=src.nodata,
                                   nodata=src.nodata if src.nodata is not None else 0) as vrt:
                        data = vrt.read().astype(dtype)
                        valid = vrt.read_masks() > 0
                if stack is None:
                    stack = np.zeros_like(data)
                    filled = np.zeros(data.shape, dtype=bool)
                    if nodata_value is not None:
                        stack[:] = nodata_value
                take = valid & ~filled
                stack[take] = data[take]
                filled |= valid
                if filled.all():
                    break
            if stack is None:
                raise ValueError(f"No scene has an asset named {asset_name!r}")
            bands.append(stack)
            eo = asset.get("eo:bands") or [{}] * stack.shape[0]
            rb = asset.get("raster:bands") or [{}] * stack.shape[0]
            for i in range(stack.shape[0]):
                names.append(asset_name if stack.shape[0] == 1 else
                             (eo[i].get("name") or eo[i].get("common_name") or f"{asset_name}_{i + 1}")
                             if i < len(eo) else f"{asset_name}_{i + 1}")
                info = rb[i] if i < len(rb) else {}
                band_info.append({k: info[k] for k in ("scale", "offset", "unit") if k in info})

    data = np.concatenate(bands, axis=0)
    metadata = {"source": "STAC", "endpoint": scenes[0].endpoint, "collection": scenes[0].collection,
                "scenes": [{"id": s.id, "datetime": s.datetime.isoformat() if s.datetime else None,
                            "cloud_cover": s.cloud_cover} for s in scenes],
                "band_info": dict(zip(names, band_info))}
    return Raster(data=data, crs=crs, transform=transform, nodata=nodata_value, band_names=names, metadata=metadata)


def build_search_body(collections, north, west, south, east, start=None, end=None, max_cloud_cover=None,
                      query=None, limit=100) -> dict:
    body = {"collections": [collections] if isinstance(collections, str) else list(collections),
            "bbox": [west, south, east, north], "limit": min(limit, 100)}
    if start or end:
        body["datetime"] = f"{_iso(start) or '..'}/{_iso(end, end_of_day=True) or '..'}"
    query = dict(query or {})
    if max_cloud_cover is not None:
        query["eo:cloud_cover"] = {"lte": max_cloud_cover}
    if query:
        body["query"] = query
    return body


def parse_item(item: dict, endpoint: str) -> Scene:
    props = item.get("properties", {})
    when = props.get("datetime") or props.get("start_datetime")
    return Scene(
        id=item["id"], collection=item.get("collection"),
        datetime=datetime.fromisoformat(when.replace("Z", "+00:00")) if when else None,
        bbox=tuple(item.get("bbox", (None,) * 4)[:4]), endpoint=endpoint,
        cloud_cover=props.get("eo:cloud_cover"), assets=item.get("assets", {}), properties=props)


# --- Planetary Computer URL signing ------------------------------------------------------------------------
_pc_tokens: Dict[str, tuple] = {}


def sign_href(scene: Scene, href: str) -> str:
    """
    Makes an asset URL readable. Items from Microsoft Planetary Computer need a short-lived SAS token, fetched
    anonymously from its token API and cached per collection; other URLs are returned unchanged.
    """
    host = urlparse(href).netloc
    if scene.endpoint.rstrip("/") != PLANETARY_COMPUTER or not host.endswith(".blob.core.windows.net") \
            or "?" in href:
        return href
    token, expiry = _pc_tokens.get(scene.collection, (None, 0))
    if token is None or expiry - time.time() < 300:
        response = requests.get(f"https://planetarycomputer.microsoft.com/api/sas/v1/token/{scene.collection}",
                                headers=HEADERS, timeout=60)
        response.raise_for_status()
        data = response.json()
        token = data["token"]
        expiry_text = data.get("msft:expiry", "")
        try:
            expiry = datetime.fromisoformat(expiry_text.replace("Z", "+00:00")).timestamp()
        except ValueError:
            expiry = time.time() + 1800
        _pc_tokens[scene.collection] = (token, expiry)
    return f"{href}?{token}"


def pick_scenes(scenes: Sequence[Scene], north: float, west: float, south: float, east: float) -> List[Scene]:
    """
    Picks the newest acquisition date that covers the box, returning all items of that date (adjacent tiles
    of one pass) with the least cloudy first. Falls back to the newest scene.
    """
    if not scenes:
        raise ValueError("No scenes found; widen the date range or the cloud limit")
    by_date: Dict[str, List[Scene]] = {}
    for scene in scenes:
        by_date.setdefault(scene.datetime.date().isoformat() if scene.datetime else "", []).append(scene)
    for day in sorted(by_date, reverse=True):
        group = sorted(by_date[day], key=lambda s: s.cloud_cover if s.cloud_cover is not None else 0)
        w = min(s.bbox[0] for s in group)
        s_ = min(s.bbox[1] for s in group)
        e = max(s.bbox[2] for s in group)
        n = max(s.bbox[3] for s in group)
        if w <= west and s_ <= south and e >= east and n >= north:
            return group
    return [scenes[0]]


def pick_clear_scenes(scenes: Sequence[Scene], north: float, west: float, south: float, east: float,
                      mask_asset: str, is_cloud: Callable[[np.ndarray], np.ndarray], max_fraction: float,
                      max_checks: int = 15) -> List[Scene]:
    """
    Picks the newest scene whose cloud mask shows at most ``max_fraction`` cloud inside the box. Scene-level
    cloud cover says little about a small area, so the mask band is read for the box itself (cheap: one band,
    a few kilobytes). Falls back to the clearest scene checked.

    :param scenes: Candidate scenes, newest first.
    :param mask_asset: Name of the cloud/quality mask asset, e.g. ``scl`` or ``qa_pixel``.
    :param is_cloud: Function mapping mask values to a boolean cloud array.
    :param max_fraction: Largest acceptable cloudy fraction, 0..1.
    :param max_checks: *(optional)* Number of candidate scenes to check. Defaults to 15.
    :return: A list with the chosen scene.
    """
    best, best_fraction = None, 2.0
    for scene in list(scenes)[:max_checks]:
        if not scene.covers(north, west, south, east) or mask_asset not in scene.assets:
            continue
        mask = read(scene, [mask_asset], north, west, south, east)
        values = mask.data[0]
        valid = values != mask.nodata if mask.nodata is not None else np.ones(values.shape, dtype=bool)
        if not valid.any():
            continue
        fraction = float(is_cloud(values[valid]).mean())
        if fraction <= max_fraction:
            return [scene]
        if fraction < best_fraction:
            best, best_fraction = scene, fraction
    if best is None:
        return pick_scenes(scenes, north, west, south, east)
    return [best]


def _asset(scene: Scene, name: str) -> dict:
    if name not in scene.assets:
        raise KeyError(f"{scene.id} has no asset {name!r}; assets: {sorted(scene.assets)}")
    return scene.assets[name]


def _next_page(page: dict, body: dict):
    for link in page.get("links", []):
        if link.get("rel") == "next":
            method = link.get("method", "GET").upper()
            if method == "POST":
                return link["href"], {**body, **link.get("body", {})}, "POST"
            return link["href"], body, "GET"
    return None, body, "POST"


def _sorted(scenes: List[Scene]) -> List[Scene]:
    return sorted(scenes, key=lambda s: s.datetime.timestamp() if s.datetime else 0, reverse=True)


def _iso(value, end_of_day: bool = False) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat().replace("+00:00", "Z") if value.tzinfo else value.isoformat() + "Z"
    text = str(value)
    if len(text) == 10:  # a plain date covers the whole day
        return text + ("T23:59:59Z" if end_of_day else "T00:00:00Z")
    return text
