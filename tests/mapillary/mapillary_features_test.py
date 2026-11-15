# Mirrorworld addition (not in upstream streetlevel). Offline: no network requests.
import base64
import json
import math
import zlib

import mapbox_vector_tile
import numpy as np
from pytest import approx

from mirrorworld import mapillary
import mirrorworld.mapillary.mapillary as mly
import mirrorworld.mapillary.parse


def test_parse_map_feature_tile():
    layer = {"name": "point", "features": [
        {"geometry": "POINT(1024 1024)", "properties": {"id": 1, "value": "object--support--utility-pole",
                                                        "first_seen_at": 1519929464142, "last_seen_at": 1519929464142}},
        {"geometry": "POINT(3072 3072)", "properties": {"id": 2, "value": "object--manhole"}}]}
    tile = mapbox_vector_tile.encode([layer], default_options={"y_coord_down": True})
    features = mapillary.parse.parse_map_feature_tile(tile, 0, 0, 1, "point")
    assert [f.value for f in features] == ["object--support--utility-pole", "object--manhole"]
    # Tile (0, 0) at zoom 1 is the north-west quadrant; the points sit a quarter and three quarters across it.
    assert features[0].lat > features[1].lat > 0
    assert features[0].lon == approx(-135.0, abs=1e-6)
    assert features[1].lon == approx(-45.0, abs=1e-6)
    assert features[0].first_seen.year == 2018


def test_parse_map_feature():
    response = {"id": "5", "object_value": "warning--turn-right--g1", "object_type": "trafficsign",
                "geometry": {"type": "Point", "coordinates": [-122.3, 47.6]},
                "first_seen_at": "2026-05-17T19:19:07+0000", "aligned_direction": 90.0,
                "images": {"data": [{"id": "7"}, {"id": "8"}]}}
    feature = mapillary.parse.parse_map_feature(response)
    assert feature.layer == "traffic_sign"
    assert feature.aligned_direction == approx(math.pi / 2)
    assert feature.image_ids == [7, 8]


def test_filter_features():
    features = mapillary.parse.parse_map_feature_tile(mapbox_vector_tile.encode([{"name": "point", "features": [
        {"geometry": "POINT(2048 2048)", "properties": {"id": 1, "value": "regulatory--stop--g1"}},
        {"geometry": "POINT(2048 2049)", "properties": {"id": 2, "value": "object--manhole"}}]}],
        default_options={"y_coord_down": True}), 0, 0, 20, "point")
    lat, lon = features[0].lat, features[0].lon
    assert [f.id for f in mly._filter_features(features, lat, lon, 50, ["regulatory--"])] == [1]
    assert [f.id for f in mly._filter_features(features, lat, lon, 50, ["object--manhole"])] == [2]
    assert len(mly._filter_features(features, lat, lon, 50, None)) == 2


def test_parse_detections():
    square = {"name": "mpy-or", "features": [{"geometry": "POLYGON((0 0, 2048 0, 2048 1024, 0 1024, 0 0))",
                                               "properties": {}}]}
    geometry = base64.b64encode(mapbox_vector_tile.encode([square], default_options={"y_coord_down": True})).decode()
    detections = mapillary.parse.parse_detections({"data": [{"id": "9", "value": "nature--sky", "geometry": geometry,
                                                             "created_at": "2025-03-03T05:26:16+0000"}]})
    assert detections[0].value == "nature--sky"
    ring = detections[0].polygons[0][0]
    xs, ys = [p[0] for p in ring], [p[1] for p in ring]
    assert (min(xs), max(xs)) == (approx(0), approx(0.5))
    assert (min(ys), max(ys)) == (approx(0), approx(0.25))   # top quarter of the image: y grows downwards


def test_parse_sfm_cluster():
    reconstruction = [{"points": {"1": {"coordinates": [0.0, 0.0, 0.0], "color": [255, 0, 0]},
                                  "2": {"coordinates": [100.0, 0.0, 10.0], "color": [0, 255, 0]}},
                       "shots": {}, "cameras": {},
                       "reference_lla": {"latitude": 47.6, "longitude": -122.3, "altitude": 20.0}}]
    cloud = mapillary.parse.parse_sfm_cluster(zlib.compress(json.dumps(reconstruction).encode()))
    assert cloud.xyz.shape == (2, 3)
    assert cloud.reference == (47.6, -122.3, 20.0)
    wgs = cloud.to_wgs84()
    assert wgs[0] == approx([47.6, -122.3, 20.0], abs=1e-6)
    assert wgs[1][1] > -122.3                      # 100 m east
    assert wgs[1][2] == approx(30.0, abs=0.01)
