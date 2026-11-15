# Mirrorworld addition (not in upstream streetlevel). Offline: no network requests.
import json
import math
from datetime import datetime, timedelta, timezone

from pytest import approx

from streetlevel import panoramax
import streetlevel.panoramax.panoramax as pmx
import streetlevel.panoramax.parse


def test_parse_panorama():
    with open("panoramax/data/find_by_id.json", "r") as f:
        response = json.load(f)

    panos = panoramax.parse.parse_feature_collection(response)
    assert len(panos) == 1
    pano = panos[0]
    assert pano.id == "eab40052-8b34-4a1b-8967-3133e78511eb"
    assert pano.lat == approx(47.6045899)
    assert pano.lon == approx(-122.3349066)
    assert pano.date == datetime(2025, 11, 1, 17, 22, 42, tzinfo=timezone(timedelta(hours=-7)))
    assert pano.heading == approx(math.radians(119))
    assert pano.is_equirectangular
    assert (pano.width, pano.height) == (5760, 2880)
    assert pano.make == "GoPro"
    assert pano.sequence_id == "028cc60a-2477-4529-9342-cb4fb72a22cd"
    assert pano.license == "CC-BY-SA-4.0"
    assert set(pano.image_urls) == {"hd", "sd", "thumb"}
    assert pano.next_id and pano.previous_id


def test_distance_filter():
    with open("panoramax/data/find_by_id.json", "r") as f:
        panos = panoramax.parse.parse_feature_collection(json.load(f))
    assert pmx._sort_by_distance(panos, 47.6045899, -122.3349066, 1)[0].distance == approx(0, abs=0.01)
    assert pmx._sort_by_distance(panos, 47.7, -122.3349066, 100) == []
    north, west, south, east = pmx._bbox_around(47.6, -122.3, 100)
    assert north > 47.6 > south and west < -122.3 < east


def test_permalink():
    assert panoramax.build_permalink("abc") == "https://api.panoramax.xyz/#focus=pic&pic=abc"
