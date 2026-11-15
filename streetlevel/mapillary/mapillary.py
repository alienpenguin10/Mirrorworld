# Mirrorworld addition (not in upstream streetlevel).
"""
Mapillary street-level imagery (https://www.mapillary.com), CC BY-SA 4.0.

Besides images, Mapillary offers map features (objects triangulated from many images, e.g. utility poles,
manholes, junction boxes, street lights, traffic signs), per-image semantic segmentations and
structure-from-motion point clouds; see :func:`find_map_features`, :func:`get_detections` and
:func:`get_point_cloud`.

Unlike most providers in this library, Mapillary has a documented public API and requires a free access
token: pass ``access_token=`` to any function or set the ``MAPILLARY_ACCESS_TOKEN`` environment variable.
"""
import math
from typing import Iterable, List, Optional, Union

import requests

from PIL import Image
from aiohttp import ClientSession
from requests import Session

from . import api
from .features import MapFeature, Detection, PointCloud
from .panorama import MapillaryPanorama
from .parse import parse_coverage_tile, parse_panorama, parse_sequence, parse_map_feature_tile, \
    parse_map_feature, parse_detections, parse_sfm_cluster
from ..exif import save_with_metadata, OutputMetadata
from ..geo import wgs84_to_tile_coord
from ..util import get_image, get_image_async

SIZES = ("256", "1024", "2048", "original")


def get_coverage_tile(tile_x: int, tile_y: int, session: Session = None,
                      access_token: str = None) -> List[MapillaryPanorama]:
    """
    Fetches all images on a Mapillary coverage tile.

    The tiles are XYZ tiles at zoom level 14 (about 1.5 km across at mid latitudes). The returned objects carry
    the location, capture time, heading, panorama flag, sequence and uploader; call
    :func:`find_panorama_by_id` for camera details and image URLs.

    :param tile_x: X coordinate of the tile.
    :param tile_y: Y coordinate of the tile.
    :param session: *(optional)* A requests session.
    :param access_token: *(optional)* Mapillary access token. Defaults to ``MAPILLARY_ACCESS_TOKEN``.
    :return: A list of MapillaryPanorama objects (empty if there is no coverage).
    """
    tile = api.get_coverage_tile(tile_x, tile_y, session, access_token)
    return parse_coverage_tile(tile, tile_x, tile_y, api.COVERAGE_ZOOM)


async def get_coverage_tile_async(tile_x: int, tile_y: int, session: ClientSession,
                                  access_token: str = None) -> List[MapillaryPanorama]:
    tile = await api.get_coverage_tile_async(tile_x, tile_y, session, access_token)
    return parse_coverage_tile(tile, tile_x, tile_y, api.COVERAGE_ZOOM)


def get_coverage_tile_by_latlon(lat: float, lon: float, session: Session = None,
                                access_token: str = None) -> List[MapillaryPanorama]:
    """
    Same as :func:`get_coverage_tile`, but for fetching the tile on which a point is located.

    :param lat: Latitude of the point.
    :param lon: Longitude of the point.
    :param session: *(optional)* A requests session.
    :param access_token: *(optional)* Mapillary access token. Defaults to ``MAPILLARY_ACCESS_TOKEN``.
    :return: A list of MapillaryPanorama objects.
    """
    tile_x, tile_y = wgs84_to_tile_coord(lat, lon, api.COVERAGE_ZOOM)
    return get_coverage_tile(tile_x, tile_y, session, access_token)


async def get_coverage_tile_by_latlon_async(lat: float, lon: float, session: ClientSession,
                                            access_token: str = None) -> List[MapillaryPanorama]:
    tile_x, tile_y = wgs84_to_tile_coord(lat, lon, api.COVERAGE_ZOOM)
    return await get_coverage_tile_async(tile_x, tile_y, session, access_token)


def find_panoramas(lat: float, lon: float, radius: float = 25, limit: Optional[int] = None,
                   panos_only: bool = False, session: Session = None,
                   access_token: str = None) -> List[MapillaryPanorama]:
    """
    Finds images within a radius around a point, closest first.

    This reads the coverage tiles that overlap the circle, because Mapillary's bounding-box search fails in
    densely covered areas.

    :param lat: Latitude of the center point.
    :param lon: Longitude of the center point.
    :param radius: *(optional)* Search radius in meters. Defaults to 25.
    :param limit: *(optional)* Maximum number of results. Defaults to no limit.
    :param panos_only: *(optional)* Only return 360° panoramas. Defaults to False.
    :param session: *(optional)* A requests session.
    :param access_token: *(optional)* Mapillary access token. Defaults to ``MAPILLARY_ACCESS_TOKEN``.
    :return: A list of MapillaryPanorama objects.
    """
    panos = []
    for tile_x, tile_y in _tiles_around(lat, lon, radius):
        panos += get_coverage_tile(tile_x, tile_y, session, access_token)
    return _filter_by_distance(panos, lat, lon, radius, limit, panos_only)


async def find_panoramas_async(lat: float, lon: float, session: ClientSession, radius: float = 25,
                               limit: Optional[int] = None, panos_only: bool = False,
                               access_token: str = None) -> List[MapillaryPanorama]:
    panos = []
    for tile_x, tile_y in _tiles_around(lat, lon, radius):
        panos += await get_coverage_tile_async(tile_x, tile_y, session, access_token)
    return _filter_by_distance(panos, lat, lon, radius, limit, panos_only)


def find_panorama_by_id(panoid: int, session: Session = None,
                        access_token: str = None) -> Optional[MapillaryPanorama]:
    """
    Fetches the full metadata of an image, including camera parameters and image URLs.

    :param panoid: The image ID.
    :param session: *(optional)* A requests session.
    :param access_token: *(optional)* Mapillary access token. Defaults to ``MAPILLARY_ACCESS_TOKEN``.
    :return: A MapillaryPanorama object, or None if no image with this ID exists.
    """
    response = api.find_panorama_by_id(panoid, session, access_token)
    return None if "error" in response else parse_panorama(response)


async def find_panorama_by_id_async(panoid: int, session: ClientSession,
                                    access_token: str = None) -> Optional[MapillaryPanorama]:
    response = await api.find_panorama_by_id_async(panoid, session, access_token)
    return None if "error" in response else parse_panorama(response)


def get_sequence(sequence_id: str, session: Session = None, access_token: str = None) -> List[int]:
    """
    Lists the IDs of the images in a sequence, in capture order.

    :param sequence_id: The sequence ID.
    :param session: *(optional)* A requests session.
    :param access_token: *(optional)* Mapillary access token. Defaults to ``MAPILLARY_ACCESS_TOKEN``.
    :return: The image IDs.
    """
    return parse_sequence(api.get_sequence(sequence_id, session, access_token))


async def get_sequence_async(sequence_id: str, session: ClientSession, access_token: str = None) -> List[int]:
    return parse_sequence(await api.get_sequence_async(sequence_id, session, access_token))


def get_panorama(pano: Union[MapillaryPanorama, int], size: str = "original", session: Session = None,
                 access_token: str = None) -> Image.Image:
    """
    Downloads an image and returns it as PIL image.

    :param pano: The image, or its ID. Metadata without image URLs (e.g. from a coverage tile) is completed
        with :func:`find_panorama_by_id` first.
    :param size: *(optional)* ``256``, ``1024``, ``2048`` (width in pixels) or ``original``.
        Defaults to ``original``.
    :param session: *(optional)* A requests session.
    :param access_token: *(optional)* Mapillary access token. Defaults to ``MAPILLARY_ACCESS_TOKEN``.
    :return: A PIL image.
    """
    size = _validate_size(size)
    pano = _with_urls(pano, session, access_token)
    return get_image(pano.image_urls[size], session)


async def get_panorama_async(pano: Union[MapillaryPanorama, int], session: ClientSession,
                             size: str = "original", access_token: str = None) -> Image.Image:
    size = _validate_size(size)
    pano = await _with_urls_async(pano, session, access_token)
    return await get_image_async(pano.image_urls[size], session)


def download_panorama(pano: Union[MapillaryPanorama, int], path: str, size: str = "original",
                      pil_args: dict = None, session: Session = None, access_token: str = None) -> None:
    """
    Downloads an image to a file. If the chosen format is JPEG, Exif metadata (and XMP GPano metadata for
    360° panoramas) is included.

    :param pano: The image, or its ID.
    :param path: Output path.
    :param size: *(optional)* ``256``, ``1024``, ``2048`` or ``original``. Defaults to ``original``.
    :param pil_args: *(optional)* Additional arguments for PIL's
        `Image.save <https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.save>`_
        method, e.g. ``{"quality":100}``. Defaults to ``{}``.
    :param session: *(optional)* A requests session.
    :param access_token: *(optional)* Mapillary access token. Defaults to ``MAPILLARY_ACCESS_TOKEN``.
    """
    if pil_args is None:
        pil_args = {}
    pano = _with_urls(pano, session, access_token)
    image = get_panorama(pano, size, session, access_token)
    save_with_metadata(image, path, pil_args, _build_output_metadata_object(pano, image))


async def download_panorama_async(pano: Union[MapillaryPanorama, int], path: str, session: ClientSession,
                                  size: str = "original", pil_args: dict = None,
                                  access_token: str = None) -> None:
    if pil_args is None:
        pil_args = {}
    pano = await _with_urls_async(pano, session, access_token)
    image = await get_panorama_async(pano, session, size, access_token)
    save_with_metadata(image, path, pil_args, _build_output_metadata_object(pano, image))


def _build_output_metadata_object(pano: MapillaryPanorama, image: Image.Image) -> OutputMetadata:
    return OutputMetadata(
        width=image.width,
        height=image.height,
        panoid=str(pano.id),
        lat=pano.lat,
        lon=pano.lon,
        creator=f"Mapillary/{pano.creator_username}" if pano.creator_username else "Mapillary",
        is_equirectangular=pano.is_equirectangular,
        altitude=pano.elevation,
        date=pano.date,
        heading=pano.heading,
    )


def _validate_size(size) -> str:
    size = str(size)
    if size not in SIZES:
        raise ValueError(f"size must be one of {SIZES}")
    return size


def _with_urls(pano, session, access_token) -> MapillaryPanorama:
    if isinstance(pano, MapillaryPanorama) and pano.image_urls:
        return pano
    panoid = pano.id if isinstance(pano, MapillaryPanorama) else pano
    full = find_panorama_by_id(panoid, session, access_token)
    if full is None:
        raise ValueError(f"No Mapillary image with ID {panoid}")
    return full


async def _with_urls_async(pano, session, access_token) -> MapillaryPanorama:
    if isinstance(pano, MapillaryPanorama) and pano.image_urls:
        return pano
    panoid = pano.id if isinstance(pano, MapillaryPanorama) else pano
    full = await find_panorama_by_id_async(panoid, session, access_token)
    if full is None:
        raise ValueError(f"No Mapillary image with ID {panoid}")
    return full


def _tiles_around(lat: float, lon: float, radius: float):
    dlat = math.degrees(radius / 6378137.0)
    dlon = dlat / max(math.cos(math.radians(lat)), 1e-6)
    x0, y0 = wgs84_to_tile_coord(lat + dlat, lon - dlon, api.COVERAGE_ZOOM)
    x1, y1 = wgs84_to_tile_coord(lat - dlat, lon + dlon, api.COVERAGE_ZOOM)
    return [(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)]


def _distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371008.8 * math.asin(math.sqrt(a))


def _filter_by_distance(panos, lat, lon, radius, limit, panos_only) -> List[MapillaryPanorama]:
    near = [(d, p) for p in panos
            if (d := _distance(lat, lon, p.lat, p.lon)) <= radius and (p.is_pano or not panos_only)]
    near.sort(key=lambda item: item[0])
    result = [p for _, p in near]
    return result[:limit] if limit else result


def get_map_features_tile(tile_x: int, tile_y: int, layer: str = "point", session: Session = None,
                          access_token: str = None) -> List[MapFeature]:
    """
    Fetches all map features (triangulated objects) on a coverage tile at zoom level 14.

    :param tile_x: X coordinate of the tile.
    :param tile_y: Y coordinate of the tile.
    :param layer: *(optional)* ``point`` (poles, manholes, junction boxes, street lights, hydrants, ...)
        or ``traffic_sign``. Defaults to ``point``.
    :param session: *(optional)* A requests session.
    :param access_token: *(optional)* Mapillary access token. Defaults to ``MAPILLARY_ACCESS_TOKEN``.
    :return: A list of MapFeature objects.
    """
    tile = api.get_map_feature_tile(tile_x, tile_y, layer, session, access_token)
    return parse_map_feature_tile(tile, tile_x, tile_y, api.COVERAGE_ZOOM, layer)


async def get_map_features_tile_async(tile_x: int, tile_y: int, session: ClientSession, layer: str = "point",
                                      access_token: str = None) -> List[MapFeature]:
    tile = await api.get_map_feature_tile_async(tile_x, tile_y, layer, session, access_token)
    return parse_map_feature_tile(tile, tile_x, tile_y, api.COVERAGE_ZOOM, layer)


def find_map_features(lat: float, lon: float, radius: float = 50, values: Optional[Iterable[str]] = None,
                      layer: str = "point", session: Session = None,
                      access_token: str = None) -> List[MapFeature]:
    """
    Finds map features (triangulated objects such as utility poles or manholes) around a point, closest first.

    :param lat: Latitude of the center point.
    :param lon: Longitude of the center point.
    :param radius: *(optional)* Search radius in meters. Defaults to 50.
    :param values: *(optional)* Keep only these classes. An entry ending in ``--`` matches as a prefix, e.g.
        ``["object--support--utility-pole", "object--manhole", "regulatory--"]``. Defaults to all.
    :param layer: *(optional)* ``point`` or ``traffic_sign``. Defaults to ``point``.
    :param session: *(optional)* A requests session.
    :param access_token: *(optional)* Mapillary access token. Defaults to ``MAPILLARY_ACCESS_TOKEN``.
    :return: A list of MapFeature objects.
    """
    features = []
    for tile_x, tile_y in _tiles_around(lat, lon, radius):
        features += get_map_features_tile(tile_x, tile_y, layer, session, access_token)
    return _filter_features(features, lat, lon, radius, values)


async def find_map_features_async(lat: float, lon: float, session: ClientSession, radius: float = 50,
                                  values: Optional[Iterable[str]] = None, layer: str = "point",
                                  access_token: str = None) -> List[MapFeature]:
    features = []
    for tile_x, tile_y in _tiles_around(lat, lon, radius):
        features += await get_map_features_tile_async(tile_x, tile_y, session, layer, access_token)
    return _filter_features(features, lat, lon, radius, values)


def find_map_feature_by_id(feature_id: int, session: Session = None,
                           access_token: str = None) -> Optional[MapFeature]:
    """
    Fetches a map feature with its facing direction and the IDs of the images it was detected in.

    :param feature_id: The map feature ID.
    :param session: *(optional)* A requests session.
    :param access_token: *(optional)* Mapillary access token. Defaults to ``MAPILLARY_ACCESS_TOKEN``.
    :return: A MapFeature object, or None if no feature with this ID exists.
    """
    response = api.find_map_feature_by_id(feature_id, session, access_token)
    return None if "error" in response else parse_map_feature(response)


async def find_map_feature_by_id_async(feature_id: int, session: ClientSession,
                                       access_token: str = None) -> Optional[MapFeature]:
    response = await api.find_map_feature_by_id_async(feature_id, session, access_token)
    return None if "error" in response else parse_map_feature(response)


def get_detections(pano: Union[MapillaryPanorama, int], session: Session = None,
                   access_token: str = None) -> List[Detection]:
    """
    Fetches Mapillary's semantic segmentation of an image: one polygon set per detected object or surface
    (road, sidewalk, curb, vegetation, sky, poles, manholes, ...).

    :param pano: The image, or its ID.
    :param session: *(optional)* A requests session.
    :param access_token: *(optional)* Mapillary access token. Defaults to ``MAPILLARY_ACCESS_TOKEN``.
    :return: A list of Detection objects with polygons in normalized image coordinates.
    """
    panoid = pano.id if isinstance(pano, MapillaryPanorama) else pano
    return parse_detections(api.get_detections(panoid, session, access_token))


async def get_detections_async(pano: Union[MapillaryPanorama, int], session: ClientSession,
                               access_token: str = None) -> List[Detection]:
    panoid = pano.id if isinstance(pano, MapillaryPanorama) else pano
    return parse_detections(await api.get_detections_async(panoid, session, access_token))


def get_point_cloud(pano: Union[MapillaryPanorama, int], session: Session = None,
                    access_token: str = None) -> Optional[PointCloud]:
    """
    Downloads the structure-from-motion reconstruction that an image belongs to: a colored point cloud of the
    surroundings plus the poses of all images in the reconstruction.

    :param pano: The image, or its ID.
    :param session: *(optional)* A requests session.
    :param access_token: *(optional)* Mapillary access token. Defaults to ``MAPILLARY_ACCESS_TOKEN``.
    :return: A PointCloud, or None if the image has no reconstruction.
    """
    panoid = pano.id if isinstance(pano, MapillaryPanorama) else pano
    cluster = api.get_sfm_cluster_url(panoid, session, access_token).get("sfm_cluster")
    if not cluster or not cluster.get("url"):
        return None
    requester = session if session else requests
    response = requester.get(cluster["url"])
    response.raise_for_status()
    return parse_sfm_cluster(response.content)


async def get_point_cloud_async(pano: Union[MapillaryPanorama, int], session: ClientSession,
                                access_token: str = None) -> Optional[PointCloud]:
    panoid = pano.id if isinstance(pano, MapillaryPanorama) else pano
    cluster = (await api.get_sfm_cluster_url_async(panoid, session, access_token)).get("sfm_cluster")
    if not cluster or not cluster.get("url"):
        return None
    async with session.get(cluster["url"]) as response:
        response.raise_for_status()
        return parse_sfm_cluster(await response.read())


def _filter_features(features, lat, lon, radius, values) -> List[MapFeature]:
    values = list(values) if values else None

    def wanted(value):
        if not values:
            return True
        return any(value.startswith(v) if v.endswith("--") else value == v for v in values)

    near = []
    for feature in features:
        feature.distance = _distance(lat, lon, feature.lat, feature.lon)
        if feature.distance <= radius and wanted(feature.value or ""):
            near.append(feature)
    return sorted(near, key=lambda f: f.distance)
