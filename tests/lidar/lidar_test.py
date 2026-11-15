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
