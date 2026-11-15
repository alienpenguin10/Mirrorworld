# Mirrorworld addition (not in upstream streetlevel). Offline: no network requests.
import json

import numpy as np
from pytest import approx

from streetlevel.raster import Raster, grid_for_bounds, utm_crs, bbox_to_crs, read_geotiff


def make():
    data = np.arange(2 * 3 * 4, dtype=np.float32).reshape(2, 3, 4)
    return Raster(data=data, crs="EPSG:32610", transform=(10.0, 0.0, 500000.0, 0.0, -10.0, 5000000.0),
                  nodata=-1.0, band_names=["a", "b"], metadata={"source": "test"})


def test_properties():
    r = make()
    assert (r.width, r.height, r.count) == (4, 3, 2)
    assert r.bounds == (500000.0, 4999970.0, 500040.0, 5000000.0)
    assert r.band("b")[0, 0] == 12


def test_grid():
    transform, w, h = grid_for_bounds((0.3, 0.2, 10.1, 5.05), 1.0)
    assert transform == (1.0, 0.0, 0.0, 0.0, -1.0, 6.0)
    assert (w, h) == (11, 6)


def test_utm():
    assert utm_crs(47.6, -122.3) == "EPSG:32610"
    assert utm_crs(-33.9, 151.2) == "EPSG:32756"
    minx, miny, maxx, maxy = bbox_to_crs(47.61, -122.34, 47.60, -122.33, "EPSG:32610")
    assert 549000 < minx < maxx < 551000 and maxy > miny


def test_save_geotiff_roundtrip(tmp_path):
    r = make()
    r.save(str(tmp_path / "r.tif"))
    back = read_geotiff((tmp_path / "r.tif").read_bytes())
    assert back.crs == "EPSG:32610"
    assert back.transform == approx(r.transform)
    assert np.array_equal(back.data, r.data)
    assert json.loads((tmp_path / "r.json").read_text())["bands"] == ["a", "b"]


def test_save_png_world_file(tmp_path):
    r = make()
    r.save(str(tmp_path / "r.png"))
    world = [float(v) for v in (tmp_path / "r.pgw").read_text().split()]
    assert world == [10.0, 0.0, 0.0, -10.0, 500005.0, 4999995.0]
    assert "EPSG:32610" in (tmp_path / "r.png.aux.xml").read_text()
    assert r.to_image().mode == "L"
