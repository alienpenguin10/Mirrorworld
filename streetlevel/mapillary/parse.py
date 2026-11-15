# Mirrorworld addition (not in upstream streetlevel).
import math
from datetime import datetime, timezone
from typing import List

import mapbox_vector_tile

import base64
import json
import zlib

import numpy as np

from .features import MapFeature, Detection, PointCloud
from .panorama import MapillaryPanorama
from ..geo import tile_coord_to_wgs84


def parse_coverage_tile(tile: bytes, tile_x: int, tile_y: int, zoom: int) -> List[MapillaryPanorama]:
    layers = mapbox_vector_tile.decode(tile, default_options={"y_coord_down": True})
    layer = layers.get("image")
    if not layer:
        return []
    extent = layer.get("extent", 4096)
    panos = []
    for feature in layer["features"]:
        px, py = feature["geometry"]["coordinates"]
        lat, lon = tile_coord_to_wgs84(tile_x + px / extent, tile_y + py / extent, zoom)
        props = feature["properties"]
        panos.append(MapillaryPanorama(
            id=int(props["id"]),
            lat=lat,
            lon=lon,
            date=_parse_timestamp(props.get("captured_at")),
            heading=_to_radians(props.get("compass_angle")),
            is_pano=props.get("is_pano"),
            sequence_id=props.get("sequence_id"),
            creator_id=props.get("creator_id"),
            organization_id=props.get("organization_id"),
            quality_score=props.get("quality_score"),
        ))
    return panos


def parse_panorama(response: dict) -> MapillaryPanorama:
    lon, lat = response["geometry"]["coordinates"]
    computed = response.get("computed_geometry")
    creator = response.get("creator") or {}
    urls = {size: response[f"thumb_{size}_url"] for size in ("256", "1024", "2048", "original")
            if response.get(f"thumb_{size}_url")}
    return MapillaryPanorama(
        id=int(response["id"]),
        lat=lat,
        lon=lon,
        date=_parse_timestamp(response.get("captured_at")),
        heading=_to_radians(response.get("compass_angle")),
        is_pano=response.get("is_pano"),
        sequence_id=response.get("sequence"),
        creator_id=int(creator["id"]) if creator.get("id") else None,
        creator_username=creator.get("username"),
        computed_lat=computed["coordinates"][1] if computed else None,
        computed_lon=computed["coordinates"][0] if computed else None,
        computed_heading=_to_radians(response.get("computed_compass_angle")),
        elevation=response.get("altitude"),
        computed_elevation=response.get("computed_altitude"),
        camera_type=response.get("camera_type"),
        camera_parameters=response.get("camera_parameters"),
        make=response.get("make"),
        model=response.get("model"),
        width=response.get("width"),
        height=response.get("height"),
        image_urls=urls or None,
    )


def parse_sequence(response: dict) -> List[int]:
    return [int(item["id"]) for item in response.get("data", [])]


def _parse_timestamp(ms) -> datetime:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc) if ms is not None else None


def _to_radians(degrees):
    return math.radians(degrees) if degrees is not None else None


def parse_map_feature_tile(tile: bytes, tile_x: int, tile_y: int, zoom: int, layer: str) -> List[MapFeature]:
    layers = mapbox_vector_tile.decode(tile, default_options={"y_coord_down": True})
    features = []
    for content in layers.values():
        extent = content.get("extent", 4096)
        for feature in content["features"]:
            if feature["geometry"]["type"] != "Point":
                continue
            px, py = feature["geometry"]["coordinates"]
            lat, lon = tile_coord_to_wgs84(tile_x + px / extent, tile_y + py / extent, zoom)
            props = feature["properties"]
            features.append(MapFeature(
                id=int(props["id"]), lat=lat, lon=lon, value=props.get("value"), layer=layer,
                first_seen=_parse_timestamp(props.get("first_seen_at")),
                last_seen=_parse_timestamp(props.get("last_seen_at")),
            ))
    return features


def parse_map_feature(response: dict) -> MapFeature:
    lon, lat = response["geometry"]["coordinates"]
    return MapFeature(
        id=int(response["id"]), lat=lat, lon=lon, value=response.get("object_value"),
        layer="traffic_sign" if response.get("object_type") == "trafficsign" else "point",
        first_seen=_parse_iso(response.get("first_seen_at")),
        last_seen=_parse_iso(response.get("last_seen_at")),
        aligned_direction=_to_radians(response.get("aligned_direction")),
        image_ids=[int(image["id"]) for image in (response.get("images") or {}).get("data", [])],
    )


def parse_detections(response: dict) -> List[Detection]:
    detections = []
    for item in response.get("data", []):
        polygons = []
        # The geometry is a base64-encoded vector tile whose extent spans the whole image.
        layers = mapbox_vector_tile.decode(base64.b64decode(item["geometry"]),
                                           default_options={"y_coord_down": True})
        for content in layers.values():
            extent = content.get("extent", 4096)
            for feature in content["features"]:
                geometry = feature["geometry"]
                parts = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
                for polygon in parts:
                    polygons.append([[(x / extent, y / extent) for x, y in ring] for ring in polygon])
        detections.append(Detection(
            id=int(item["id"]), value=item.get("value"),
            polygons=polygons,
            created_at=_parse_iso(item.get("created_at")),
        ))
    return detections


def parse_sfm_cluster(data: bytes) -> PointCloud:
    reconstructions = json.loads(zlib.decompress(data))
    reconstruction = reconstructions[0] if isinstance(reconstructions, list) else reconstructions
    points = reconstruction.get("points", {})
    xyz = np.array([p["coordinates"] for p in points.values()], dtype=np.float64).reshape(-1, 3)
    rgb = np.array([p.get("color", [0, 0, 0]) for p in points.values()], dtype=np.float64).reshape(-1, 3)
    ref = reconstruction.get("reference_lla", {})
    return PointCloud(xyz=xyz, rgb=rgb,
                      reference=(ref.get("latitude"), ref.get("longitude"), ref.get("altitude")),
                      reconstruction=reconstruction)


def _parse_iso(value):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z")
