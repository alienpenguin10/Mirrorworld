# Mirrorworld addition (not in upstream streetlevel). Offline: no network requests.
from datetime import datetime, timezone

from mirrorworld.satellite import stac
from mirrorworld.satellite.scene import Scene


def scene(id, day, bbox=(-123, 47, -122, 48), cloud=5.0):
    return Scene(id=id, collection="c", datetime=datetime(2025, 7, day, tzinfo=timezone.utc), bbox=bbox,
                 endpoint="e", cloud_cover=cloud)


def test_search_body():
    body = stac.build_search_body("sentinel-2-l2a", 48, -123, 47, -122, "2025-06-01", "2025-06-30", 20, None, 50)
    assert body["collections"] == ["sentinel-2-l2a"]
    assert body["bbox"] == [-123, 47, -122, 48]
    assert body["datetime"] == "2025-06-01T00:00:00Z/2025-06-30T23:59:59Z"
    assert body["query"] == {"eo:cloud_cover": {"lte": 20}}
    assert "datetime" not in stac.build_search_body("c", 1, 0, 0, 1)


def test_parse_item():
    item = {"id": "x", "collection": "naip", "bbox": [1, 2, 3, 4],
            "properties": {"datetime": "2023-10-07T00:00:00Z", "eo:cloud_cover": 1.5}, "assets": {"image": {"href": "h"}}}
    s = stac.parse_item(item, "endpoint")
    assert s.datetime == datetime(2023, 10, 7, tzinfo=timezone.utc)
    assert s.cloud_cover == 1.5 and s.assets["image"]["href"] == "h"
    assert s.covers(3.5, 1.5, 2.5, 2.5) and not s.covers(5, 1, 2, 2)


def test_pick_scenes():
    newest_partial = scene("a", 20, bbox=(-122.5, 47, -122, 48))
    older_full = scene("b", 10)
    picked = stac.pick_scenes([newest_partial, older_full], 47.7, -122.8, 47.5, -122.2)
    assert [s.id for s in picked] == ["b"]
    # Two adjacent tiles of the same day together cover the box.
    left, right = scene("l", 25, bbox=(-123, 47, -122.5, 48)), scene("r", 25, bbox=(-122.5, 47, -122, 48), cloud=1)
    assert [s.id for s in stac.pick_scenes([left, right, older_full], 47.7, -122.8, 47.5, -122.2)] == ["r", "l"]


def test_sign_leaves_other_hosts():
    s = scene("a", 1)
    assert stac.sign_href(s, "https://sentinel-cogs.s3.us-west-2.amazonaws.com/x.tif") == \
        "https://sentinel-cogs.s3.us-west-2.amazonaws.com/x.tif"


def test_sentinel2_offset_fix():
    import numpy as np
    from mirrorworld.raster import Raster
    from mirrorworld.satellite import sentinel2
    r = Raster(data=np.zeros((1, 1, 1)), crs="EPSG:32630", transform=(10, 0, 0, 0, -10, 0),
               metadata={"band_info": {"red": {"scale": 0.0001, "offset": -0.1}}})
    applied = scene("a", 1); applied.properties = {"earthsearch:boa_offset_applied": True}
    sentinel2.fix_offsets(r, [applied])
    assert r.metadata["band_info"]["red"] == {"scale": 0.0001, "offset": 0.0}
    r.metadata["band_info"]["red"]["offset"] = -0.1
    sentinel2.fix_offsets(r, [scene("b", 2)])                 # flag absent: leave the catalogue's offset
    assert r.metadata["band_info"]["red"]["offset"] == -0.1
