# Mirrorworld addition (not in upstream streetlevel).
from aiohttp import ClientSession
from requests import Session
import requests

from .util import get_access_token
from ..util import get_json, get_json_async

COVERAGE_ZOOM = 14
"""Zoom level of the coverage tiles that carry individual images."""

IMAGE_FIELDS = ",".join([
    "id", "geometry", "computed_geometry", "captured_at", "compass_angle", "computed_compass_angle",
    "altitude", "computed_altitude", "is_pano", "camera_type", "camera_parameters", "make", "model",
    "width", "height", "sequence", "creator", "thumb_256_url", "thumb_1024_url", "thumb_2048_url",
    "thumb_original_url",
])


def _headers(access_token: str = None) -> dict:
    return {"Authorization": f"OAuth {get_access_token(access_token)}"}


def build_coverage_tile_request_url(tile_x: int, tile_y: int, access_token: str = None) -> str:
    return f"https://tiles.mapillary.com/maps/vtp/mly1_public/2/{COVERAGE_ZOOM}/{tile_x}/{tile_y}" \
           f"?access_token={get_access_token(access_token)}"


def build_find_panorama_by_id_request_url(panoid: int) -> str:
    return f"https://graph.mapillary.com/{panoid}?fields={IMAGE_FIELDS}"


def build_sequence_request_url(sequence_id: str) -> str:
    return f"https://graph.mapillary.com/image_ids?sequence_id={sequence_id}"


def get_coverage_tile(tile_x: int, tile_y: int, session: Session = None, access_token: str = None) -> bytes:
    requester = session if session else requests
    response = requester.get(build_coverage_tile_request_url(tile_x, tile_y, access_token))
    response.raise_for_status()
    return response.content


async def get_coverage_tile_async(tile_x: int, tile_y: int, session: ClientSession,
                                  access_token: str = None) -> bytes:
    async with session.get(build_coverage_tile_request_url(tile_x, tile_y, access_token)) as response:
        response.raise_for_status()
        return await response.read()


def find_panorama_by_id(panoid: int, session: Session = None, access_token: str = None) -> dict:
    return get_json(build_find_panorama_by_id_request_url(panoid), session, headers=_headers(access_token))


async def find_panorama_by_id_async(panoid: int, session: ClientSession, access_token: str = None) -> dict:
    return await get_json_async(build_find_panorama_by_id_request_url(panoid), session,
                                headers=_headers(access_token))


def get_sequence(sequence_id: str, session: Session = None, access_token: str = None) -> dict:
    return get_json(build_sequence_request_url(sequence_id), session, headers=_headers(access_token))


async def get_sequence_async(sequence_id: str, session: ClientSession, access_token: str = None) -> dict:
    return await get_json_async(build_sequence_request_url(sequence_id), session, headers=_headers(access_token))


MAP_FEATURE_LAYERS = {"point": "mly_map_feature_point", "traffic_sign": "mly_map_feature_traffic_sign"}
MAP_FEATURE_FIELDS = "id,object_value,object_type,geometry,first_seen_at,last_seen_at,aligned_direction,images"


def build_map_feature_tile_request_url(tile_x: int, tile_y: int, layer: str, access_token: str = None) -> str:
    if layer not in MAP_FEATURE_LAYERS:
        raise ValueError(f"layer must be one of {tuple(MAP_FEATURE_LAYERS)}")
    return f"https://tiles.mapillary.com/maps/vtp/{MAP_FEATURE_LAYERS[layer]}/2/{COVERAGE_ZOOM}/{tile_x}/{tile_y}" \
           f"?access_token={get_access_token(access_token)}"


def build_map_feature_request_url(feature_id: int) -> str:
    return f"https://graph.mapillary.com/{feature_id}?fields={MAP_FEATURE_FIELDS}"


def build_detections_request_url(panoid: int) -> str:
    return f"https://graph.mapillary.com/{panoid}/detections?fields=id,value,geometry,created_at"


def build_sfm_request_url(panoid: int) -> str:
    return f"https://graph.mapillary.com/{panoid}?fields=sfm_cluster"


def get_map_feature_tile(tile_x: int, tile_y: int, layer: str, session: Session = None,
                         access_token: str = None) -> bytes:
    requester = session if session else requests
    response = requester.get(build_map_feature_tile_request_url(tile_x, tile_y, layer, access_token))
    response.raise_for_status()
    return response.content


async def get_map_feature_tile_async(tile_x: int, tile_y: int, layer: str, session: ClientSession,
                                     access_token: str = None) -> bytes:
    async with session.get(build_map_feature_tile_request_url(tile_x, tile_y, layer, access_token)) as response:
        response.raise_for_status()
        return await response.read()


def find_map_feature_by_id(feature_id: int, session: Session = None, access_token: str = None) -> dict:
    return get_json(build_map_feature_request_url(feature_id), session, headers=_headers(access_token))


async def find_map_feature_by_id_async(feature_id: int, session: ClientSession, access_token: str = None) -> dict:
    return await get_json_async(build_map_feature_request_url(feature_id), session, headers=_headers(access_token))


def get_detections(panoid: int, session: Session = None, access_token: str = None) -> dict:
    return get_json(build_detections_request_url(panoid), session, headers=_headers(access_token))


async def get_detections_async(panoid: int, session: ClientSession, access_token: str = None) -> dict:
    return await get_json_async(build_detections_request_url(panoid), session, headers=_headers(access_token))


def get_sfm_cluster_url(panoid: int, session: Session = None, access_token: str = None) -> dict:
    return get_json(build_sfm_request_url(panoid), session, headers=_headers(access_token))


async def get_sfm_cluster_url_async(panoid: int, session: ClientSession, access_token: str = None) -> dict:
    return await get_json_async(build_sfm_request_url(panoid), session, headers=_headers(access_token))
