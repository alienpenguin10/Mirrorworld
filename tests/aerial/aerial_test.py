# Mirrorworld addition (not in upstream streetlevel). Offline: no network requests.
import json

from PIL import Image
from pytest import approx, raises

from mirrorworld.aerial import bing, esri, google, usgs
from mirrorworld.aerial.dataclasses import AerialImage
from mirrorworld.aerial.util import bbox_to_pixels, ground_resolution, pixel_to_wgs84, save_aerial_image, \
    tiles_in_pixel_window, wgs84_to_pixel, zoom_for_resolution, TileResponse
import mirrorworld.aerial.bing.bing
import mirrorworld.aerial.google.google


def test_quadkey_roundtrip():
    assert bing.to_quadkey(3, 5, 3) == "213"
    assert bing.from_quadkey("213") == (3, 5, 3)
    assert bing.from_quadkey(bing.to_quadkey(167969, 366207, 20)) == (167969, 366207, 20)


def test_resolution():
    assert ground_resolution(0, 0) == approx(156543.034, rel=1e-6)
    assert ground_resolution(47.6062, 20) == approx(0.1007, abs=1e-4)
    assert zoom_for_resolution(47.6062, 0.10) == 20
    assert zoom_for_resolution(47.6062, 0.20) == 19


def test_pixel_roundtrip():
    x, y = wgs84_to_pixel(47.6062, -122.3321, 20)
    lat, lon = pixel_to_wgs84(x, y, 20)
    assert lat == approx(47.6062, abs=1e-9)
    assert lon == approx(-122.3321, abs=1e-9)


def test_tiles_in_window():
    left, top, right, bottom = bbox_to_pixels(47.6070, -122.3345, 47.6055, -122.3320, 20)
    tiles = tiles_in_pixel_window(left, top, right, bottom)
    assert tiles[0] == (left // 256, top // 256)
    assert tiles[-1] == ((right - 1) // 256, (bottom - 1) // 256)
    with raises(ValueError):
        bbox_to_pixels(47.6, -122.3, 47.7, -122.2, 20)


def test_missing_rules():
    no_tile = TileResponse(0, 0, 200, {"x-ve-tile-info": "no-tile"}, b"")
    ok = TileResponse(0, 0, 200, {}, b"")
    assert mirrorworld.aerial.bing.bing._is_missing(no_tile)
    assert not mirrorworld.aerial.bing.bing._is_missing(ok)
    assert mirrorworld.aerial.google.google._is_missing(TileResponse(0, 0, 404, {}, b""))


def test_tile_urls():
    assert bing.api.build_tile_url(3, 5, 3).startswith("https://ecn.t0.tiles.virtualearth.net/tiles/a213.jpeg?g=")
    assert google.api.build_tile_url(3, 5, 3) == "https://mt0.google.com/vt/lyrs=s&x=3&y=5&z=3"
    assert esri.api.build_tile_url(3, 5, 3).endswith("/World_Imagery/MapServer/tile/3/5/3")
    assert usgs.api.build_tile_url(3, 5, 3).endswith("/USGSImageryOnly/MapServer/tile/3/5/3")


def test_save_aerial_image(tmp_path):
    aerial = AerialImage(image=Image.new("RGB", (4, 2)), provider="test", zoom=20,
                         north=1.0, west=0.0, south=0.0, east=1.0,
                         origin_x=100.0, origin_y=200.0, mercator_resolution=0.5, ground_resolution=0.5,
                         tile_count=1, metadata={"k": ["v"]})
    save_aerial_image(aerial, str(tmp_path / "a.png"))
    world = (tmp_path / "a.pgw").read_text().split()
    assert [float(v) for v in world] == [0.5, 0.0, 0.0, -0.5, 100.25, 199.75]
    assert "EPSG:3857" in (tmp_path / "a.png.aux.xml").read_text()
    assert json.loads((tmp_path / "a.json").read_text())["metadata"] == {"k": ["v"]}
