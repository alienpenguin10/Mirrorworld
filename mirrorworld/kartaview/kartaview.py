# Mirrorworld addition (not in upstream streetlevel).
"""
KartaView street-level imagery (https://kartaview.org, formerly OpenStreetCam), CC BY-SA 4.0.
The API is public and needs no key.
"""
import math
from io import BytesIO
from typing import List, Optional, Union

import requests
from PIL import Image
from aiohttp import ClientSession
from requests import Session

from . import api
from .panorama import KartaViewPanorama
from .parse import parse_panoramas, parse_panorama_response, has_more_data
from ..exif import save_with_metadata, OutputMetadata

PAGE_SIZE = 100
SIZES = ("full", "large", "small")


def find_panoramas(lat: float, lon: float, radius: float = 25, limit: Optional[int] = 100,
                   session: Session = None) -> List[KartaViewPanorama]:
    """
    Finds photos within a radius around a point, closest first.

    :param lat: Latitude of the center point.
    :param lon: Longitude of the center point.
    :param radius: *(optional)* Search radius in meters. Defaults to 25.
    :param limit: *(optional)* Maximum number of results. Defaults to 100.
    :param session: *(optional)* A requests session.
    :return: A list of KartaViewPanorama objects.
    """
    panos, page = [], 1
    while True:
        response = api.find_panoramas(lat, lon, radius, page, PAGE_SIZE, session)
        panos += parse_panoramas(response)
        if not has_more_data(response):
            break
        page += 1
    return _sort_and_limit(panos, lat, lon, radius, limit)


async def find_panoramas_async(lat: float, lon: float, session: ClientSession, radius: float = 25,
                               limit: Optional[int] = 100) -> List[KartaViewPanorama]:
    panos, page = [], 1
    while True:
        response = await api.find_panoramas_async(lat, lon, radius, page, PAGE_SIZE, session)
        panos += parse_panoramas(response)
        if not has_more_data(response):
            break
        page += 1
    return _sort_and_limit(panos, lat, lon, radius, limit)


def find_panorama_by_id(panoid: int, session: Session = None) -> Optional[KartaViewPanorama]:
    """
    Fetches metadata of a specific photo.

    :param panoid: The photo ID.
    :param session: *(optional)* A requests session.
    :return: A KartaViewPanorama object, or None if no photo with this ID exists.
    """
    return parse_panorama_response(api.find_panorama_by_id(panoid, session))


async def find_panorama_by_id_async(panoid: int, session: ClientSession) -> Optional[KartaViewPanorama]:
    return parse_panorama_response(await api.find_panorama_by_id_async(panoid, session))


def get_sequence(sequence_id: int, session: Session = None) -> List[KartaViewPanorama]:
    """
    Fetches all photos of a sequence (track), in capture order.

    :param sequence_id: The sequence ID.
    :param session: *(optional)* A requests session.
    :return: A list of KartaViewPanorama objects.
    """
    panos, page = [], 1
    while True:
        response = api.get_sequence_photos(sequence_id, page, PAGE_SIZE, session)
        panos += parse_panoramas(response)
        if not has_more_data(response):
            break
        page += 1
    return sorted(panos, key=lambda p: p.sequence_index or 0)


async def get_sequence_async(sequence_id: int, session: ClientSession) -> List[KartaViewPanorama]:
    panos, page = [], 1
    while True:
        response = await api.get_sequence_photos_async(sequence_id, page, PAGE_SIZE, session)
        panos += parse_panoramas(response)
        if not has_more_data(response):
            break
        page += 1
    return sorted(panos, key=lambda p: p.sequence_index or 0)


def get_panorama(pano: Union[KartaViewPanorama, int], size: str = "full", session: Session = None) -> Image.Image:
    """
    Downloads a photo and returns it as PIL image.

    :param pano: The photo, or its ID.
    :param size: *(optional)* ``full``, ``large`` (large thumbnail) or ``small`` (thumbnail).
        Defaults to ``full``.
    :param session: *(optional)* A requests session.
    :return: A PIL image.
    """
    if not isinstance(pano, KartaViewPanorama):
        pano = _require(find_panorama_by_id(pano, session), pano)
    errors = []
    for url in _image_urls(pano, size):
        requester = session if session else requests
        response = requester.get(url)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
        errors.append(f"{url}: HTTP {response.status_code}")
    raise RuntimeError(f"Photo {pano.id} could not be downloaded: " + "; ".join(errors))


async def get_panorama_async(pano: Union[KartaViewPanorama, int], session: ClientSession,
                             size: str = "full") -> Image.Image:
    if not isinstance(pano, KartaViewPanorama):
        pano = _require(await find_panorama_by_id_async(pano, session), pano)
    errors = []
    for url in _image_urls(pano, size):
        async with session.get(url) as response:
            if response.status == 200:
                return Image.open(BytesIO(await response.read()))
            errors.append(f"{url}: HTTP {response.status}")
    raise RuntimeError(f"Photo {pano.id} could not be downloaded: " + "; ".join(errors))


def download_panorama(pano: Union[KartaViewPanorama, int], path: str, size: str = "full",
                      pil_args: dict = None, session: Session = None) -> None:
    """
    Downloads a photo to a file. If the chosen format is JPEG, Exif metadata (and XMP GPano metadata for
    360° panoramas) is included.

    :param pano: The photo, or its ID.
    :param path: Output path.
    :param size: *(optional)* ``full``, ``large`` or ``small``. Defaults to ``full``.
    :param pil_args: *(optional)* Additional arguments for PIL's
        `Image.save <https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.save>`_
        method, e.g. ``{"quality":100}``. Defaults to ``{}``.
    :param session: *(optional)* A requests session.
    """
    if pil_args is None:
        pil_args = {}
    if not isinstance(pano, KartaViewPanorama):
        pano = _require(find_panorama_by_id(pano, session), pano)
    image = get_panorama(pano, size, session)
    save_with_metadata(image, path, pil_args, _build_output_metadata_object(pano, image))


async def download_panorama_async(pano: Union[KartaViewPanorama, int], path: str, session: ClientSession,
                                  size: str = "full", pil_args: dict = None) -> None:
    if pil_args is None:
        pil_args = {}
    if not isinstance(pano, KartaViewPanorama):
        pano = _require(await find_panorama_by_id_async(pano, session), pano)
    image = await get_panorama_async(pano, session, size)
    save_with_metadata(image, path, pil_args, _build_output_metadata_object(pano, image))


def _build_output_metadata_object(pano: KartaViewPanorama, image: Image.Image) -> OutputMetadata:
    return OutputMetadata(
        width=image.width,
        height=image.height,
        panoid=str(pano.id),
        lat=pano.lat,
        lon=pano.lon,
        creator="KartaView",
        is_equirectangular=pano.is_equirectangular,
        date=pano.date,
        heading=pano.heading,
    )


def _image_urls(pano: KartaViewPanorama, size: str) -> List[str]:
    if size not in SIZES:
        raise ValueError(f"size must be one of {SIZES}")
    urls = (pano.image_urls or {}).get(size)
    if not urls:
        raise ValueError(f"Photo {pano.id} has no {size} image URL")
    return urls


def _require(pano, panoid):
    if pano is None:
        raise ValueError(f"No KartaView photo with ID {panoid}")
    return pano


def _sort_and_limit(panos: List[KartaViewPanorama], lat: float, lon: float, radius: float,
                    limit: Optional[int]) -> List[KartaViewPanorama]:
    # The API's own "distance" field does not match the coordinates it returns, so recompute it.
    for pano in panos:
        pano.distance = _distance(lat, lon, pano.lat, pano.lon)
    near = sorted((p for p in panos if p.distance <= radius), key=lambda p: p.distance)
    return near[:limit] if limit else near


def _distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371008.8 * math.asin(math.sqrt(a))
