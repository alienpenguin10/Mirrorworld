# Mirrorworld addition (not in upstream streetlevel). Offline: no network requests.
from io import BytesIO

import laspy
import numpy as np
from pytest import approx

from mirrorworld.lidar import ept, usgs3dep


def test_node_bounds():
    cube = (0.0, 0.0, 0.0, 8.0, 8.0, 8.0)
    assert ept.node_bounds(cube, "0-0-0-0") == (0.0, 0.0, 8.0, 8.0)
    assert ept.node_bounds(cube, "1-1-0-0") == (4.0, 0.0, 8.0, 4.0)
    assert ept.node_bounds(cube, "2-3-3-1") == (6.0, 6.0, 8.0, 8.0)
    assert ept.node_intersects(cube, "1-1-1-0", (5, 5, 6, 6))
    assert not ept.node_intersects(cube, "1-0-0-0", (5, 5, 6, 6))


def test_depth_for_resolution():
    info = ept.EptInfo(url="u", bounds=(0, 0, 0, 1280, 1280, 1280), bounds_conforming=(0,) * 6, span=128,
                       points=1, crs="EPSG:3857", schema=[])
    assert info.spacing(0) == 10.0
    assert info.depth_for_resolution(10.0) == 0
    assert info.depth_for_resolution(1.0) == 4      # 10 / 2**4 = 0.625 <= 1


def _laz(xs, ys, classes, offset=0.0):
    header = laspy.LasHeader(point_format=6, version="1.4")
    header.scales = np.array([0.01, 0.01, 0.01])
    header.offsets = np.array([offset, offset, 0.0])
    las = laspy.LasData(header)
    las.x, las.y, las.z = np.array(xs, float), np.array(ys, float), np.zeros(len(xs))
    las.classification = np.array(classes, np.uint8)
    buffer = BytesIO()
    las.write(buffer)
    return buffer.getvalue()


def test_merge_nodes():
    a = _laz([1.0, 5.0], [1.0, 5.0], [2, 6])
    b = _laz([2.0, 9.0], [2.0, 9.0], [6, 6], offset=100.0)   # different offset: re-quantized
    merged = ept.merge_nodes(laspy, [a, b], (0, 0, 6, 6), "EPSG:3857", None)
    assert sorted(merged.x) == approx([1.0, 2.0, 5.0])
    buildings = ept.merge_nodes(laspy, [a, b], (0, 0, 6, 6), None, [6])
    assert sorted(buildings.x) == approx([2.0, 5.0])


def test_boundary_intersection():
    square = {"type": "Polygon", "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]]}
    assert usgs3dep._intersects(square, 6, 4, 5, 5)          # box inside
    assert usgs3dep._intersects(square, 12, -2, -2, 12)      # box contains polygon
    assert not usgs3dep._intersects(square, 22, 20, 21, 21)


# --- Environment Agency NLP tiles (lidar.ea) ---

import json

from mirrorworld.lidar import ea


def test_ea_tile_name():
    assert ea.tile_name(541000, 257500) == "TL4055"
    assert ea.tile_name(545000, 255000) == "TL4555"
    assert ea.tile_name(405000, 290000) == "SP0590"
    assert ea.tile_name(529999.9, 179999.9) == "TQ2575"
    assert ea.tile_name(445000, 1210000) == "HP4510"


def test_ea_tile_bounds_roundtrip():
    for tile in ["TL4055", "SP0590", "TQ2575", "HP4510", "SV9505", "NO5045"]:
        minx, miny, maxx, maxy = ea.tile_bounds(tile)
        assert maxx - minx == 5000 and maxy - miny == 5000
        assert ea.tile_name(minx + 1, miny + 1) == tile


class _Response:
    def __init__(self, body=b"", status=200, payload=None):
        self.body, self.status_code, self.headers, self.payload = body, status, {}, payload

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)

    def iter_content(self, size):
        return iter([self.body[i:i + size] for i in range(0, len(self.body), size)])

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def _result(product, year, tile, res="1"):
    return {"product": {"id": product}, "year": {"id": str(year)}, "resolution": {"id": res},
            "tile": {"id": tile, "label": "x"}, "label": f"{product}-{year}",
            "uri": f"https://environment.data.gov.uk/tiles/collections/survey/{product}/{year}/{res}/{tile}"}


SEARCH = {"count": 4, "results": [_result(ea.PRODUCT, 2019, "TL4055"), _result("lidar_composite_dtm", 2022, "TL4055"),
                                  _result(ea.PRODUCT, 2023, "TL4055"), _result(ea.PRODUCT, 2020, "TL4555")]}


def test_ea_search_filters_and_sorts(monkeypatch):
    sent = {}

    def fake_request(method, url, **kwargs):
        sent.update(method=method, url=url, body=json.loads(kwargs["data"]))
        return _Response(payload=SEARCH)

    monkeypatch.setattr(ea.requests, "request", fake_request)
    tiles = ea.search(52.21, 0.10, 52.20, 0.12)
    assert [(t.tile, t.year) for t in tiles] == [("TL4055", 2023), ("TL4055", 2019), ("TL4555", 2020)]
    assert sent["method"] == "POST" and sent["url"] == ea.SEARCH_URL
    assert sent["body"]["coordinates"][0][0] == [0.10, 52.20]
    assert len(ea.search(52.21, 0.10, 52.20, 0.12, product=None)) == 4
    assert ea.find_years("tl4055") == [2023, 2019]


def test_ea_retries_rate_limit(monkeypatch):
    answers = iter([_Response(b"too many", status=429), _Response(payload=SEARCH)])
    monkeypatch.setattr(ea.requests, "request", lambda *a, **k: next(answers))
    monkeypatch.setattr(ea.time, "sleep", lambda s: None)
    assert len(ea.search(52.21, 0.10, 52.20, 0.12)) == 3


def test_ea_download_tile_keeps_provider_name(tmp_path, monkeypatch):
    import zipfile
    from io import BytesIO
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("TL4055_P_12744_20230213_20230213.laz", _laz([541000.0], [257000.0], [2]))
    zipped = buffer.getvalue()

    def fake_request(method, url, **kwargs):
        return _Response(payload=SEARCH) if method == "POST" else _Response(zipped)

    monkeypatch.setattr(ea.requests, "request", fake_request)
    path = ea.download_tile("TL4055", directory=str(tmp_path))
    assert path == str(tmp_path / ea.PRODUCT / "2023" / "TL4055_P_12744_20230213_20230213.laz")
    assert len(laspy.read(path).points) == 1
    assert sorted(p.name for p in (tmp_path / ea.PRODUCT / "2023").iterdir()) == [
        "TL4055_P_12744_20230213_20230213.laz"]   # no zip or partial files left


def test_ea_download_tile_uses_cache(tmp_path, monkeypatch):
    folder = tmp_path / ea.PRODUCT / "2023"
    folder.mkdir(parents=True)
    (folder / "TL4055_P_12744_20230213_20230213.laz").write_bytes(b"")
    monkeypatch.setattr(ea.requests, "request", lambda *a, **k: (_ for _ in ()).throw(AssertionError("network")))
    assert ea.download_tile("TL4055", 2023, str(tmp_path)).endswith("TL4055_P_12744_20230213_20230213.laz")


def test_ea_crop_files(tmp_path):
    a, b = tmp_path / "a.laz", tmp_path / "b.laz"
    a.write_bytes(_laz([541000.01, 541010.0, 541500.0], [257000.0, 257010.0, 257500.0], [2, 6, 2], offset=540000.0))
    b.write_bytes(_laz([545005.0], [257005.0], [6], offset=545000.0))
    las = ea.crop_files([str(a), str(b)], (540990, 256990, 545010, 257020), chunk_size=2)
    assert sorted(las.x) == approx([541000.01, 541010.0, 545005.0])
    assert ea.crop_files([str(a), str(b)], (540990, 256990, 545010, 257020), classes=[6]).x == approx(
        [541010.0, 545005.0])


def test_ea_crop_files_mixed_point_formats(tmp_path):
    header = laspy.LasHeader(point_format=1, version="1.2")
    header.scales, header.offsets = np.array([0.01, 0.01, 0.01]), np.array([540000.0, 255000.0, 0.0])
    old = laspy.LasData(header)
    old.x, old.y, old.z = np.array([541000.0]), np.array([257000.0]), np.array([10.0])
    old.classification = np.array([2], np.uint8)
    a, b = tmp_path / "old.laz", tmp_path / "new.laz"
    old.write(str(a))
    b.write_bytes(_laz([545005.0], [257005.0], [6], offset=545000.0))   # LAS 1.4, point format 6
    las = ea.crop_files([str(b), str(a)], (540990, 256990, 545010, 257020))
    assert las.header.point_format.id == 6
    assert sorted(las.x) == approx([541000.0, 545005.0])
    assert sorted(las.classification) == [2, 6]
    las.write(str(tmp_path / "merged.laz"))
    assert len(laspy.read(str(tmp_path / "merged.laz")).points) == 2
