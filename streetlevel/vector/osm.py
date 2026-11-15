# Mirrorworld addition (not in upstream streetlevel).
"""
OpenStreetMap features through the Overpass API, as GeoJSON: e.g. sidewalks, surface tags, street cabinets,
utility poles, buildings, land use. Data (c) OpenStreetMap contributors, ODbL. No key; please keep requests
modest or point ``endpoint`` at your own Overpass instance for bulk work.
"""
import asyncio
import json
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Union

import requests
from aiohttp import ClientSession, ClientTimeout

DEFAULT_ENDPOINT = "https://overpass-api.de/api/interpreter"
HEADERS = {"User-Agent": "streetlevel (Python)"}
AREA_KEYS = {"building", "landuse", "natural", "leisure", "amenity", "area", "water", "place", "parking",
             "surface", "landcover", "man_made", "aeroway", "shop", "tourism", "boundary", "highway:area"}
"""Tags whose closed ways are areas (polygons) rather than lines."""

RETRIES = 5
RETRY_STATUSES = {429, 502, 503, 504}
"""Overpass answers these when busy or rate limiting; requests are retried with backoff."""

TagFilter = Union[Dict[str, Union[str, bool, Iterable[str]]], Iterable[str]]


def build_query(north: float, west: float, south: float, east: float, tags: TagFilter, timeout: int = 180) -> str:
    """
    Builds an Overpass QL query for nodes, ways and relations matching any of the tag filters in a box.

    :param tags: Either a dict, where each entry is one alternative: ``{"power": "pole"}`` (exact value),
        ``{"highway": ["footway", "path"]}`` (any of the values), ``{"building": True}`` (any value);
        or a list of raw Overpass filters, e.g. ``['["footway"="sidewalk"]["surface"]']``.
    :return: The query text.
    """
    bbox = f"({south},{west},{north},{east})"
    filters = []
    if isinstance(tags, dict):
        for key, value in tags.items():
            if value is True:
                filters.append(f'["{key}"]')
            elif isinstance(value, str):
                filters.append(f'["{key}"="{value}"]')
            else:
                filters.append(f'["{key}"~"^({"|".join(value)})$"]')
    else:
        filters = list(tags)
    body = "".join(f"nwr{f}{bbox};" for f in filters)
    return f"[out:json][timeout:{timeout}];({body});out geom tags;"


def query(ql: str, endpoint: str = DEFAULT_ENDPOINT, session: requests.Session = None) -> dict:
    """
    Runs a raw Overpass QL query.

    :param ql: The query, which should request ``[out:json]``.
    :param endpoint: *(optional)* Overpass interpreter URL.
    :param session: *(optional)* A requests session.
    :return: The Overpass JSON response.
    """
    requester = session if session else requests
    for attempt in range(RETRIES):
        response = requester.post(endpoint, data={"data": ql}, headers=HEADERS, timeout=300)
        if response.status_code not in RETRY_STATUSES or attempt == RETRIES - 1:
            response.raise_for_status()
            return response.json()
        time.sleep(_retry_delay(response.headers.get("Retry-After"), attempt))


async def query_async(ql: str, session: ClientSession, endpoint: str = DEFAULT_ENDPOINT) -> dict:
    for attempt in range(RETRIES):
        async with session.post(endpoint, data={"data": ql}, headers=HEADERS,
                                timeout=ClientTimeout(total=300)) as response:
            if response.status not in RETRY_STATUSES or attempt == RETRIES - 1:
                response.raise_for_status()
                return await response.json(content_type=None)
            delay = _retry_delay(response.headers.get("Retry-After"), attempt)
        await asyncio.sleep(delay)


def find_features(north: float, west: float, south: float, east: float, tags: TagFilter,
                  endpoint: str = DEFAULT_ENDPOINT, session: requests.Session = None) -> dict:
    """
    Fetches OSM features matching tag filters inside a bounding box as a GeoJSON FeatureCollection.

    Nodes become Points, ways LineStrings (or Polygons when closed and area-like, see :data:`AREA_KEYS`),
    multipolygon relations MultiPolygons. Each feature's properties hold its OSM tags plus ``@id``
    (e.g. ``way/123``). Ways and relations are returned whole, so they may extend beyond the box.

    :param north: Latitude of the top edge.
    :param west: Longitude of the left edge.
    :param south: Latitude of the bottom edge.
    :param east: Longitude of the right edge.
    :param tags: Tag filters; see :func:`build_query`.
    :param endpoint: *(optional)* Overpass interpreter URL.
    :param session: *(optional)* A requests session.
    :return: A GeoJSON FeatureCollection (dict).
    """
    return to_geojson(query(build_query(north, west, south, east, tags), endpoint, session))


async def find_features_async(north: float, west: float, south: float, east: float, tags: TagFilter,
                              session: ClientSession, endpoint: str = DEFAULT_ENDPOINT) -> dict:
    return to_geojson(await query_async(build_query(north, west, south, east, tags), session, endpoint))


def download_features(north: float, west: float, south: float, east: float, tags: TagFilter, path: str,
                      **kwargs) -> dict:
    """
    Same as :func:`find_features`, then writes a GeoJSON file.

    :param path: Output path.
    :return: The FeatureCollection.
    """
    collection = find_features(north, west, south, east, tags, **kwargs)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(collection))
    return collection


def to_geojson(response: dict) -> dict:
    """Converts an Overpass ``out geom`` JSON response to a GeoJSON FeatureCollection."""
    features = []
    for element in response.get("elements", []):
        geometry = _geometry(element)
        if geometry is None:
            continue
        properties = dict(element.get("tags", {}))
        properties["@id"] = f"{element['type']}/{element['id']}"
        features.append({"type": "Feature", "geometry": geometry, "properties": properties})
    return {"type": "FeatureCollection", "features": features,
            "attribution": "(c) OpenStreetMap contributors, ODbL"}


def _geometry(element: dict) -> Optional[dict]:
    kind = element["type"]
    if kind == "node":
        return {"type": "Point", "coordinates": [element["lon"], element["lat"]]}
    if kind == "way":
        coords = [[p["lon"], p["lat"]] for p in element.get("geometry", []) if p]
        if len(coords) < 2:
            return None
        tags = element.get("tags", {})
        closed = coords[0] == coords[-1] and len(coords) >= 4
        if closed and tags.get("area") != "no" and (tags.get("area") == "yes" or AREA_KEYS & tags.keys()):
            return {"type": "Polygon", "coordinates": [coords]}
        return {"type": "LineString", "coordinates": coords}
    if kind == "relation" and element.get("tags", {}).get("type") in ("multipolygon", "boundary"):
        outers = _rings([m for m in element.get("members", []) if m.get("role") in ("outer", "")])
        inners = _rings([m for m in element.get("members", []) if m.get("role") == "inner"])
        if not outers:
            return None
        polygons = [[outer] for outer in outers]
        for inner in inners:
            # Assign each hole to the first outer ring containing its first vertex.
            for polygon in polygons:
                if _in_ring(inner[0], polygon[0]):
                    polygon.append(inner)
                    break
        return {"type": "MultiPolygon", "coordinates": polygons}
    return None


def _rings(members: List[dict]) -> List[List[List[float]]]:
    """Joins member ways end to end into closed rings."""
    segments = [[[p["lon"], p["lat"]] for p in m.get("geometry", []) if p] for m in members
                if m.get("type") == "way"]
    segments = [s for s in segments if len(s) >= 2]
    rings = []
    while segments:
        ring = segments.pop(0)
        changed = True
        while ring[0] != ring[-1] and changed:
            changed = False
            for i, seg in enumerate(segments):
                if seg[0] == ring[-1]:
                    ring += seg[1:]
                elif seg[-1] == ring[-1]:
                    ring += seg[::-1][1:]
                elif seg[-1] == ring[0]:
                    ring = seg[:-1] + ring
                elif seg[0] == ring[0]:
                    ring = seg[::-1][:-1] + ring
                else:
                    continue
                segments.pop(i)
                changed = True
                break
        if ring[0] == ring[-1] and len(ring) >= 4:
            rings.append(ring)
    return rings


def _in_ring(point, ring) -> bool:
    x, y = point
    inside = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def _retry_delay(retry_after: Optional[str], attempt: int) -> float:
    try:
        return min(float(retry_after), 60.0)
    except (TypeError, ValueError):
        return min(5.0 * 2 ** attempt, 60.0)
