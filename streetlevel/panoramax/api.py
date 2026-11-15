# Mirrorworld addition (not in upstream streetlevel).
from aiohttp import ClientSession
from requests import Session

from .util import DEFAULT_API_URL
from ..util import get_json, get_json_async


def build_find_panoramas_in_bbox_request_url(north: float, west: float, south: float, east: float, limit: int,
                                             api_url: str = DEFAULT_API_URL) -> str:
    return f"{api_url}/search?bbox={west},{south},{east},{north}&limit={limit}"


def build_find_panorama_by_id_request_url(panoid: str, api_url: str = DEFAULT_API_URL) -> str:
    return f"{api_url}/search?ids={panoid}"


def build_sequence_request_url(sequence_id: str, limit: int, api_url: str = DEFAULT_API_URL) -> str:
    return f"{api_url}/collections/{sequence_id}/items?limit={limit}"


def get(url: str, session: Session = None) -> dict:
    return get_json(url, session)


async def get_async(url: str, session: ClientSession) -> dict:
    return await get_json_async(url, session, json_function_parameters={"content_type": None})
