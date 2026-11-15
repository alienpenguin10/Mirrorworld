# Mirrorworld addition (not in upstream streetlevel).
from aiohttp import ClientSession
from requests import Session

from ..util import get_json, get_json_async

API_URL = "https://api.kartaview.org/2.0"
# The former api.openstreetcam.org host no longer serves a valid certificate.


def build_find_panoramas_request_url(lat: float, lon: float, radius: float, page: int, per_page: int) -> str:
    return f"{API_URL}/photo/?lat={lat}&lng={lon}&radius={radius}&page={page}&itemsPerPage={per_page}"


def build_find_panorama_by_id_request_url(panoid: int) -> str:
    return f"{API_URL}/photo/{panoid}"


def build_sequence_photos_request_url(sequence_id: int, page: int, per_page: int) -> str:
    return f"{API_URL}/photo/?sequenceId={sequence_id}&page={page}&itemsPerPage={per_page}"


def find_panoramas(lat: float, lon: float, radius: float, page: int, per_page: int,
                   session: Session = None) -> dict:
    return get_json(build_find_panoramas_request_url(lat, lon, radius, page, per_page), session)


async def find_panoramas_async(lat: float, lon: float, radius: float, page: int, per_page: int,
                               session: ClientSession) -> dict:
    return await get_json_async(build_find_panoramas_request_url(lat, lon, radius, page, per_page), session)


def find_panorama_by_id(panoid: int, session: Session = None) -> dict:
    return get_json(build_find_panorama_by_id_request_url(panoid), session)


async def find_panorama_by_id_async(panoid: int, session: ClientSession) -> dict:
    return await get_json_async(build_find_panorama_by_id_request_url(panoid), session)


def get_sequence_photos(sequence_id: int, page: int, per_page: int, session: Session = None) -> dict:
    return get_json(build_sequence_photos_request_url(sequence_id, page, per_page), session)


async def get_sequence_photos_async(sequence_id: int, page: int, per_page: int, session: ClientSession) -> dict:
    return await get_json_async(build_sequence_photos_request_url(sequence_id, page, per_page), session)
