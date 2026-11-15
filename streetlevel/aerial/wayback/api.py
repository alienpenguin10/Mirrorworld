# Mirrorworld addition (not in upstream streetlevel).
import asyncio

from aiohttp import ClientSession, ClientTimeout, ClientError

from ..util import HEADERS

CONFIG_URL = "https://s3-us-west-2.amazonaws.com/config.maptiles.arcgis.com/waybackconfig.json"
SERVICE_URL = "https://wayback.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/MapServer"


def build_tilemap_url(release_id: int, x: int, y: int, zoom: int, width: int = 1, height: int = 1) -> str:
    return f"{SERVICE_URL}/tilemap/{release_id}/{zoom}/{y}/{x}/{height}/{width}"


def build_metadata_query_url(metadata_url: str, zoom: int) -> str:
    # One metadata layer per zoom level: layer 0 describes zoom 23 (1.9 cm), layer 13 zoom 10 and below.
    layer = min(max(23 - zoom, 0), 13)
    return f"{metadata_url}/{layer}/query"


async def get_config_async(session: ClientSession) -> dict:
    async with session.get(CONFIG_URL, headers=HEADERS) as response:
        response.raise_for_status()
        return await response.json(content_type=None)


async def get_tilemap_async(release_id: int, x: int, y: int, zoom: int, session: ClientSession,
                            width: int = 1, height: int = 1) -> dict:
    async with session.get(build_tilemap_url(release_id, x, y, zoom, width, height), headers=HEADERS) as response:
        if response.status != 200:
            return {}
        return await response.json(content_type=None)


async def query_metadata_async(metadata_url: str, lat: float, lon: float, zoom: int,
                               session: ClientSession) -> dict:
    params = {"f": "json", "geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint", "inSR": "4326",
              "spatialRel": "esriSpatialRelIntersects", "outFields": "*", "returnGeometry": "false"}
    # Some metadata services occasionally hang; a short timeout with retries keeps lookups fast.
    for _ in range(3):
        try:
            async with session.get(build_metadata_query_url(metadata_url, zoom), params=params, headers=HEADERS,
                                   timeout=ClientTimeout(total=10)) as response:
                if response.status != 200:
                    return {}
                return await response.json(content_type=None)
        except (asyncio.TimeoutError, ClientError):
            continue
    return {}
