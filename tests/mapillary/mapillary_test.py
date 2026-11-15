# Mirrorworld addition (not in upstream streetlevel). Offline: no network requests.
import json
import math
from datetime import datetime, timezone

import mapbox_vector_tile
from pytest import approx, raises

from streetlevel import mapillary
import streetlevel.mapillary.parse


def test_parse_panorama():
    with open("mapillary/data/find_by_id.json", "r") as f:
        response = json.load(f)

    pano = mapillary.parse.parse_panorama(response)
    assert pano.id == 1340409547112764
    assert pano.lat == approx(47.613605049999)
    assert pano.lon == approx(-122.33747545)
    assert pano.computed_lat == approx(47.61330278683)
    assert pano.heading == approx(math.radians(199.44884715931))
    assert pano.computed_heading == approx(math.radians(345.22861852953))
    assert pano.date == datetime(2016, 1, 1, 4, 5, 51, 567000, tzinfo=timezone.utc)
    assert pano.is_pano and pano.is_equirectangular
    assert pano.camera_type == "spherical"
    assert pano.make == "GoPro"
    assert pano.width == 4096
    assert pano.sequence_id == "bD0VKNSGxOtUTIRPaEYLdB"
    assert pano.creator_username == "pedestrian_mapping"
    assert set(pano.image_urls) == {"256", "1024", "2048", "original"}


def test_parse_coverage_tile():
    # A synthetic tile with one image in the middle of tile (2, 1) at zoom 2.
    layer = {"name": "image", "features": [{
        "geometry": "POINT(2048 2048)",
        "properties": {"id": 42, "captured_at": 1579454155690, "compass_angle": 90.0, "is_pano": False,
                       "sequence_id": "abc", "creator_id": 7, "quality_score": 0.5}}]}
    tile = mapbox_vector_tile.encode([layer], default_options={"y_coord_down": True})

    panos = mapillary.parse.parse_coverage_tile(tile, 2, 1, 2)
    assert len(panos) == 1
    assert panos[0].id == 42
    assert panos[0].lon == approx(45.0, abs=1e-6)
    assert panos[0].lat > 0
    assert panos[0].heading == approx(math.pi / 2)
    assert panos[0].sequence_id == "abc"
    assert mapillary.parse.parse_coverage_tile(mapbox_vector_tile.encode([]), 0, 0, 0) == []


def test_parse_sequence():
    assert mapillary.parse.parse_sequence({"data": [{"id": "1"}, {"id": "2"}]}) == [1, 2]


def test_permalink():
    assert mapillary.build_permalink(id=5) == "https://www.mapillary.com/app/?pKey=5"
    assert "lat=1&lng=2" in mapillary.build_permalink(lat=1, lon=2)
    with raises(ValueError):
        mapillary.build_permalink()


def test_access_token(monkeypatch):
    monkeypatch.delenv("MAPILLARY_ACCESS_TOKEN", raising=False)
    with raises(ValueError):
        mapillary.get_access_token()
    assert mapillary.get_access_token("MLY|x") == "MLY|x"
    monkeypatch.setenv("MAPILLARY_ACCESS_TOKEN", "MLY|env")
    assert mapillary.get_access_token() == "MLY|env"
