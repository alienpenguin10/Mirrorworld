# Mirrorworld addition (not in upstream streetlevel).
"""
Panoramax (https://panoramax.fr), the federated open street-level imagery platform, CC BY-SA 4.0 for most
pictures. No key is needed. By default the federated catalogue ``api.panoramax.xyz`` is queried, which covers
all public instances; pass ``api_url=`` to query one instance directly.
"""
import math
from typing import List, Optional, Union

from PIL import Image
from aiohttp import ClientSession
from requests import Session

from . import api
from .panorama import PanoramaxPanorama
from .parse import parse_feature_collection, get_next_link
from .util import DEFAULT_API_URL
from ..exif import save_with_metadata, OutputMetadata
from ..util import get_image, get_image_async

SIZES = ("hd", "sd", "thumb")
MAX_LIMIT = 10000


def find_panoramas(lat: float, lon: float, radius: float = 25, limit: int = 100, session: Session = None,
                   api_url: str = DEFAULT_API_URL) -> List[PanoramaxPanorama]:
    """
    Finds pictures taken within a radius around a point, closest first.

    (Panoramax's own ``place_position`` search returns pictures *looking at* a place instead, which is not
    what this function does.)

    :param lat: Latitude of the center point.
    :param lon: Longitude of the center point.
    :param radius: *(optional)* Search radius in meters. Defaults to 25.
    :param limit: *(optional)* Maximum number of results. Defaults to 100.
    :param session: *(optional)* A requests session.
    :param api_url: *(optional)* Panoramax API to query. Defaults to the federated catalogue.
    :return: A list of PanoramaxPanorama objects.
    """
    url = api.build_find_panoramas_in_bbox_request_url(*_bbox_around(lat, lon, radius), MAX_LIMIT, api_url)
    return _sort_by_distance(parse_feature_collection(api.get(url, session)), lat, lon, radius)[:limit]


async def find_panoramas_async(lat: float, lon: float, session: ClientSession, radius: float = 25,
                               limit: int = 100, api_url: str = DEFAULT_API_URL) -> List[PanoramaxPanorama]:
    url = api.build_find_panoramas_in_bbox_request_url(*_bbox_around(lat, lon, radius), MAX_LIMIT, api_url)
    return _sort_by_distance(parse_feature_collection(await api.get_async(url, session)), lat, lon, radius)[:limit]


def find_panoramas_in_bbox(north: float, west: float, south: float, east: float, limit: int = 1000,
                           session: Session = None, api_url: str = DEFAULT_API_URL) -> List[PanoramaxPanorama]:
    """
    Finds pictures within a bounding box.

    :param north: Latitude of the top edge.
    :param west: Longitude of the left edge.
    :param south: Latitude of the bottom edge.
    :param east: Longitude of the right edge.
    :param limit: *(optional)* Maximum number of results, at most 10000. Defaults to 1000.
        Split large areas, since results beyond the limit are dropped.
    :param session: *(optional)* A requests session.
    :param api_url: *(optional)* Panoramax API to query. Defaults to the federated catalogue.
    :return: A list of PanoramaxPanorama objects.
    """
    url = api.build_find_panoramas_in_bbox_request_url(north, west, south, east, min(limit, MAX_LIMIT), api_url)
    return parse_feature_collection(api.get(url, session))


async def find_panoramas_in_bbox_async(north: float, west: float, south: float, east: float,
                                       session: ClientSession, limit: int = 1000,
                                       api_url: str = DEFAULT_API_URL) -> List[PanoramaxPanorama]:
    url = api.build_find_panoramas_in_bbox_request_url(north, west, south, east, min(limit, MAX_LIMIT), api_url)
    return parse_feature_collection(await api.get_async(url, session))


def find_panorama_by_id(panoid: str, session: Session = None,
                        api_url: str = DEFAULT_API_URL) -> Optional[PanoramaxPanorama]:
    """
    Fetches metadata of a specific picture.

    :param panoid: The picture ID.
    :param session: *(optional)* A requests session.
    :param api_url: *(optional)* Panoramax API to query. Defaults to the federated catalogue.
    :return: A PanoramaxPanorama object, or None if no picture with this ID exists.
    """
    panos = parse_feature_collection(api.get(api.build_find_panorama_by_id_request_url(panoid, api_url), session))
    return panos[0] if panos else None


async def find_panorama_by_id_async(panoid: str, session: ClientSession,
                                    api_url: str = DEFAULT_API_URL) -> Optional[PanoramaxPanorama]:
    response = await api.get_async(api.build_find_panorama_by_id_request_url(panoid, api_url), session)
    panos = parse_feature_collection(response)
    return panos[0] if panos else None


def get_sequence(sequence_id: str, session: Session = None,
                 api_url: str = DEFAULT_API_URL) -> List[PanoramaxPanorama]:
    """
    Fetches all pictures of a sequence, in capture order.

    :param sequence_id: The sequence (collection) ID.
    :param session: *(optional)* A requests session.
    :param api_url: *(optional)* Panoramax API to query. Defaults to the federated catalogue.
    :return: A list of PanoramaxPanorama objects.
    """
    panos, url = [], api.build_sequence_request_url(sequence_id, 1000, api_url)
    while url:
        response = api.get(url, session)
        panos += parse_feature_collection(response)
        url = get_next_link(response)
    return sorted(panos, key=lambda p: p.rank_in_sequence or 0)


async def get_sequence_async(sequence_id: str, session: ClientSession,
                             api_url: str = DEFAULT_API_URL) -> List[PanoramaxPanorama]:
    panos, url = [], api.build_sequence_request_url(sequence_id, 1000, api_url)
    while url:
        response = await api.get_async(url, session)
        panos += parse_feature_collection(response)
        url = get_next_link(response)
    return sorted(panos, key=lambda p: p.rank_in_sequence or 0)


def get_panorama(pano: Union[PanoramaxPanorama, str], size: str = "hd", session: Session = None) -> Image.Image:
    """
    Downloads a picture and returns it as PIL image.

    :param pano: The picture, or its ID.
    :param size: *(optional)* ``hd`` (original resolution), ``sd`` or ``thumb``. Defaults to ``hd``.
    :param session: *(optional)* A requests session.
    :return: A PIL image.
    """
    if not isinstance(pano, PanoramaxPanorama):
        pano = _require(find_panorama_by_id(pano, session), pano)
    return get_image(_image_url(pano, size), session)


async def get_panorama_async(pano: Union[PanoramaxPanorama, str], session: ClientSession,
                             size: str = "hd") -> Image.Image:
    if not isinstance(pano, PanoramaxPanorama):
        pano = _require(await find_panorama_by_id_async(pano, session), pano)
    return await get_image_async(_image_url(pano, size), session)


def download_panorama(pano: Union[PanoramaxPanorama, str], path: str, size: str = "hd", pil_args: dict = None,
                      session: Session = None) -> None:
    """
    Downloads a picture to a file. If the chosen format is JPEG, Exif metadata (and XMP GPano metadata for
    360° panoramas) is included.

    :param pano: The picture, or its ID.
    :param path: Output path.
    :param size: *(optional)* ``hd``, ``sd`` or ``thumb``. Defaults to ``hd``.
    :param pil_args: *(optional)* Additional arguments for PIL's
        `Image.save <https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.save>`_
        method, e.g. ``{"quality":100}``. Defaults to ``{}``.
    :param session: *(optional)* A requests session.
    """
    if pil_args is None:
        pil_args = {}
    if not isinstance(pano, PanoramaxPanorama):
        pano = _require(find_panorama_by_id(pano, session), pano)
    image = get_panorama(pano, size, session)
    save_with_metadata(image, path, pil_args, _build_output_metadata_object(pano, image))


async def download_panorama_async(pano: Union[PanoramaxPanorama, str], path: str, session: ClientSession,
                                  size: str = "hd", pil_args: dict = None) -> None:
    if pil_args is None:
        pil_args = {}
    if not isinstance(pano, PanoramaxPanorama):
        pano = _require(await find_panorama_by_id_async(pano, session), pano)
    image = await get_panorama_async(pano, session, size)
    save_with_metadata(image, path, pil_args, _build_output_metadata_object(pano, image))


def _build_output_metadata_object(pano: PanoramaxPanorama, image: Image.Image) -> OutputMetadata:
    return OutputMetadata(
        width=image.width,
        height=image.height,
        panoid=pano.id,
        lat=pano.lat,
        lon=pano.lon,
        creator=f"Panoramax/{pano.producer}" if pano.producer else "Panoramax",
        is_equirectangular=pano.is_equirectangular,
        date=pano.date,
        heading=pano.heading,
        pitch=pano.pitch,
        roll=pano.roll,
    )


def _image_url(pano: PanoramaxPanorama, size: str) -> str:
    if size not in SIZES:
        raise ValueError(f"size must be one of {SIZES}")
    url = (pano.image_urls or {}).get(size)
    if not url:
        raise ValueError(f"Picture {pano.id} has no {size} image")
    return url


def _require(pano, panoid):
    if pano is None:
        raise ValueError(f"No Panoramax picture with ID {panoid}")
    return pano


def _bbox_around(lat: float, lon: float, radius: float):
    dlat = math.degrees(radius / 6378137.0)
    dlon = dlat / max(math.cos(math.radians(lat)), 1e-6)
    return lat + dlat, lon - dlon, lat - dlat, lon + dlon


def _sort_by_distance(panos: List[PanoramaxPanorama], lat: float, lon: float,
                      radius: float) -> List[PanoramaxPanorama]:
    for pano in panos:
        p1, p2 = math.radians(lat), math.radians(pano.lat)
        a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(pano.lon - lon) / 2) ** 2
        pano.distance = 2 * 6371008.8 * math.asin(math.sqrt(a))
    return sorted((p for p in panos if p.distance <= radius), key=lambda p: p.distance)
