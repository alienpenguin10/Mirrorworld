# Mirrorworld addition (not in upstream streetlevel). Offline: no network requests.
import json
import math
from datetime import datetime

from pytest import approx

from streetlevel import kartaview
import streetlevel.kartaview.kartaview
import streetlevel.kartaview.parse


def test_parse_panoramas():
    with open("kartaview/data/find.json", "r") as f:
        response = json.load(f)

    panos = kartaview.parse.parse_panoramas(response)
    assert [p.id for p in panos] == [15825033, 182960067]
    assert panos[0].lat == approx(47.606233)
    assert panos[0].lon == approx(-122.332151)
    assert all(len(p.image_urls["full"]) == 2 for p in panos)


def test_parse_panorama():
    with open("kartaview/data/find_by_id.json", "r") as f:
        response = json.load(f)

    pano = kartaview.parse.parse_panorama_response(response)
    assert pano.id == 2625911756
    assert pano.lat == approx(47.604935)
    assert pano.lon == approx(-122.332603)
    assert pano.heading == approx(math.radians(327.5))
    assert pano.date == datetime(2025, 9, 1, 17, 56, 33)
    assert pano.sequence_id == 11606856
    assert pano.sequence_index == 56
    assert pano.field_of_view == 360
    assert pano.is_equirectangular
    assert pano.way_id == 357831864
    assert pano.matched_lat == approx(47.605106353759766)
    assert pano.image_urls["full"][0].startswith("https://storage")
    assert pano.image_urls["full"][1].startswith("https://cdn.kartaview.org/")
    assert pano.permalink == "https://kartaview.org/details/11606856/56/track-info"


def test_missing_photo():
    assert kartaview.parse.parse_panorama_response({"status": {}, "result": {"data": None}}) is None


def test_sort_and_limit():
    with open("kartaview/data/find.json", "r") as f:
        panos = kartaview.parse.parse_panoramas(json.load(f))
    near = streetlevel.kartaview.kartaview._sort_and_limit(panos, 47.6062, -122.3321, 10, None)
    assert [p.id for p in near] == [15825033]
    assert near[0].distance == approx(5.1, abs=0.5)
