# Mirrorworld addition (not in upstream streetlevel).
"""
Esri World Imagery Wayback: every archived release of Esri World Imagery since 2014, for change detection
and multi-temporal studies.

Releases are published every few weeks, but most of them leave any given place unchanged.
:func:`find_versions` lists only the releases that actually changed the imagery at a location, with the
capture date of each.
"""
import asyncio
import re
from datetime import date, datetime
from typing import List, Optional, Union

from aiohttp import ClientSession

from . import api
from .release import WaybackRelease, WaybackVersion
from ..dataclasses import AerialImage
from ..util import TileResponse, TILE_SIZE, DEFAULT_MAX_TILES, DEFAULT_MAX_CONCURRENCY, bbox_to_pixels, \
    get_tiled_image_async, run_sync, save_aerial_image, wgs84_to_pixel

PROVIDER = "Esri World Imagery Wayback"
MAX_ZOOM = 23
TILEMAP_BLOCK = 64


def get_releases() -> List[WaybackRelease]:
    """
    Lists all archived releases of Esri World Imagery, newest first.

    :return: A list of WaybackRelease objects.
    """
    return run_sync(get_releases_async)


async def get_releases_async(session: ClientSession) -> List[WaybackRelease]:
    return parse_config(await api.get_config_async(session))


def parse_config(config: dict) -> List[WaybackRelease]:
    """Parses the Wayback configuration document into releases, newest first."""
    releases = []
    for key, item in config.items():
        match = re.search(r"(\d{4}-\d{2}-\d{2})", item.get("itemTitle", ""))
        if not match:
            continue
        releases.append(WaybackRelease(
            id=int(key),
            date=datetime.strptime(match.group(1), "%Y-%m-%d").date(),
            title=item["itemTitle"],
            tile_url_template=item["itemURL"],
            metadata_url=item.get("metadataLayerUrl"),
        ))
    releases.sort(key=lambda r: r.date, reverse=True)
    return releases


def find_versions(lat: float, lon: float, zoom: int = 19) -> List[WaybackVersion]:
    """
    Lists the distinct versions of the imagery at a location, newest first, each with its capture date.
    Releases that re-publish an unchanged capture are merged (see :func:`merge_versions`).

    :param lat: Latitude.
    :param lon: Longitude.
    :param zoom: *(optional)* Zoom level to check. Defaults to 19 (≈0.3 m at the equator).
    :return: A list of WaybackVersion objects. Capture metadata stays None where Esri's metadata service
        does not answer.
    """
    return run_sync(find_versions_async, lat, lon, zoom=zoom)


async def find_versions_async(lat: float, lon: float, session: ClientSession,
                              zoom: int = 19) -> List[WaybackVersion]:
    releases = await get_releases_async(session)
    by_id = {r.id: r for r in releases}
    x, y = _tile_at(lat, lon, zoom)
    sources, index = [], 0
    while index < len(releases):
        tilemap = await api.get_tilemap_async(releases[index].id, x, y, zoom, session)
        if not tilemap.get("data") or not tilemap["data"][0]:
            break
        # "select" names the release whose imagery this release still serves at this tile.
        source_id = (tilemap.get("select") or [releases[index].id])[0]
        source = by_id.get(source_id, releases[index])
        sources.append(source)
        older = [i for i, r in enumerate(releases) if r.date < source.date]
        if not older:
            break
        index = older[0]
    described = await asyncio.gather(*(_describe_version_async(s, lat, lon, zoom, session) for s in sources))
    return merge_versions(list(described))


def merge_versions(versions: List[WaybackVersion]) -> List[WaybackVersion]:
    """
    Merges consecutive versions (newest first) with the same capture date: Esri regularly re-publishes (and
    sometimes re-processes, changing the reported resolution) an unchanged capture in a new release. Each
    merged entry keeps the oldest release, i.e. the one that introduced the capture. Versions without capture
    metadata are never merged.
    """
    merged: List[WaybackVersion] = []
    for version in versions:
        previous = merged[-1] if merged else None
        if previous is not None and version.capture_date is not None and \
                previous.capture_date == version.capture_date:
            merged[-1] = version
        else:
            merged.append(version)
    return merged


def get_image(north: float, west: float, south: float, east: float,
              release: Union[WaybackRelease, int, None] = None, zoom: int = 19,
              max_tiles: int = DEFAULT_MAX_TILES,
              max_concurrency: int = DEFAULT_MAX_CONCURRENCY) -> AerialImage:
    """
    Downloads the imagery of one release inside a bounding box and stitches it into one image.

    :param north: Latitude of the top edge.
    :param west: Longitude of the left edge.
    :param south: Latitude of the bottom edge.
    :param east: Longitude of the right edge.
    :param release: *(optional)* A release from :func:`get_releases` or :func:`find_versions`, or its ID.
        Defaults to the newest release.
    :param zoom: *(optional)* Zoom level. Defaults to 19.
    :param max_tiles: *(optional)* Refuse requests covering more tiles than this. Defaults to 20000.
    :param max_concurrency: *(optional)* Maximum number of simultaneous requests. Defaults to 8.
    :return: The stitched image; ``metadata`` names the release.
    """
    return run_sync(get_image_async, north, west, south, east, release=release, zoom=zoom,
                    max_tiles=max_tiles, max_concurrency=max_concurrency)


async def get_image_async(north: float, west: float, south: float, east: float, session: ClientSession,
                          release: Union[WaybackRelease, int, None] = None, zoom: int = 19,
                          max_tiles: int = DEFAULT_MAX_TILES,
                          max_concurrency: int = DEFAULT_MAX_CONCURRENCY) -> AerialImage:
    release = await _resolve_release_async(release, session)
    left, top, right, bottom = bbox_to_pixels(north, west, south, east, zoom)
    missing = await _find_missing_tiles_async(release.id, left, top, right, bottom, zoom, session)
    aerial = await get_tiled_image_async(
        north, west, south, east, zoom, PROVIDER,
        lambda x, y: release.tile_url_template.format(level=zoom, row=y, col=x), _is_missing, session,
        skip_tiles=missing, max_tiles=max_tiles, max_concurrency=max_concurrency)
    aerial.metadata.update({"release_id": release.id, "release_date": release.date.isoformat(),
                            "release_title": release.title})
    return aerial


def download_image(north: float, west: float, south: float, east: float, path: str,
                   release: Union[WaybackRelease, int, None] = None, zoom: int = 19, pil_args: dict = None,
                   max_tiles: int = DEFAULT_MAX_TILES,
                   max_concurrency: int = DEFAULT_MAX_CONCURRENCY) -> AerialImage:
    """
    Downloads the imagery of one release inside a bounding box to a georeferenced file
    (see :func:`streetlevel.aerial.util.save_aerial_image`).

    :param north: Latitude of the top edge.
    :param west: Longitude of the left edge.
    :param south: Latitude of the bottom edge.
    :param east: Longitude of the right edge.
    :param path: Output path.
    :param release: *(optional)* A release or release ID. Defaults to the newest release.
    :param zoom: *(optional)* Zoom level. Defaults to 19.
    :param pil_args: *(optional)* Additional arguments for PIL's ``Image.save`` method.
    :param max_tiles: *(optional)* Refuse requests covering more tiles than this. Defaults to 20000.
    :param max_concurrency: *(optional)* Maximum number of simultaneous requests. Defaults to 8.
    :return: The stitched image.
    """
    aerial = get_image(north, west, south, east, release, zoom, max_tiles, max_concurrency)
    save_aerial_image(aerial, path, pil_args)
    return aerial


async def download_image_async(north: float, west: float, south: float, east: float, path: str,
                               session: ClientSession, release: Union[WaybackRelease, int, None] = None,
                               zoom: int = 19, pil_args: dict = None, max_tiles: int = DEFAULT_MAX_TILES,
                               max_concurrency: int = DEFAULT_MAX_CONCURRENCY) -> AerialImage:
    aerial = await get_image_async(north, west, south, east, session, release, zoom, max_tiles, max_concurrency)
    save_aerial_image(aerial, path, pil_args)
    return aerial


async def _describe_version_async(release: WaybackRelease, lat: float, lon: float, zoom: int,
                                  session: ClientSession) -> WaybackVersion:
    version = WaybackVersion(release=release)
    if not release.metadata_url:
        return version
    response = await api.query_metadata_async(release.metadata_url, lat, lon, zoom, session)
    features = response.get("features") or []
    if features:
        attributes = features[0].get("attributes", {})
        version.capture_date = _parse_yyyymmdd(attributes.get("SRC_DATE"))
        version.resolution = attributes.get("SRC_RES")
        version.accuracy = attributes.get("SRC_ACC")
        version.source = attributes.get("NICE_NAME")
        version.provider = attributes.get("NICE_DESC")
    return version


async def _resolve_release_async(release, session) -> WaybackRelease:
    if isinstance(release, WaybackVersion):
        return release.release
    if isinstance(release, WaybackRelease):
        return release
    releases = await get_releases_async(session)
    if release is None:
        return releases[0]
    for candidate in releases:
        if candidate.id == int(release):
            return candidate
    raise ValueError(f"Unknown Wayback release {release}")


async def _find_missing_tiles_async(release_id, left, top, right, bottom, zoom, session):
    tx0, ty0 = left // TILE_SIZE, top // TILE_SIZE
    tx1, ty1 = (right - 1) // TILE_SIZE, (bottom - 1) // TILE_SIZE
    missing = set()
    for by in range(ty0, ty1 + 1, TILEMAP_BLOCK):
        for bx in range(tx0, tx1 + 1, TILEMAP_BLOCK):
            width, height = min(TILEMAP_BLOCK, tx1 - bx + 1), min(TILEMAP_BLOCK, ty1 - by + 1)
            flags = (await api.get_tilemap_async(release_id, bx, by, zoom, session, width, height)).get("data") or []
            for j in range(height):
                for i in range(width):
                    k = j * width + i
                    if k >= len(flags) or not flags[k]:
                        missing.add((bx + i, by + j))
    return missing


def _is_missing(response: TileResponse) -> bool:
    return response.status == 404


def _parse_yyyymmdd(value) -> Optional[date]:
    try:
        return datetime.strptime(str(int(value)), "%Y%m%d").date()
    except (TypeError, ValueError):
        return None


def _tile_at(lat: float, lon: float, zoom: int):
    px, py = wgs84_to_pixel(lat, lon, zoom)
    return int(px // TILE_SIZE), int(py // TILE_SIZE)
