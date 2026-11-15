# Mirrorworld addition (not in upstream streetlevel). Offline: no network requests.
from streetlevel.vector import osm


def test_build_query():
    q = osm.build_query(2, 1, 0, 3, {"power": "pole", "highway": ["footway", "path"], "building": True})
    assert q.startswith("[out:json]")
    assert 'nwr["power"="pole"](0,1,2,3);' in q
    assert 'nwr["highway"~"^(footway|path)$"](0,1,2,3);' in q
    assert 'nwr["building"](0,1,2,3);' in q
    assert 'nwr["footway"="sidewalk"](0,1,2,3);' in osm.build_query(2, 1, 0, 3, ['["footway"="sidewalk"]'])


def test_to_geojson():
    square = [{"lat": 0, "lon": 0}, {"lat": 0, "lon": 1}, {"lat": 1, "lon": 1}, {"lat": 1, "lon": 0}, {"lat": 0, "lon": 0}]
    response = {"elements": [
        {"type": "node", "id": 1, "lat": 1.5, "lon": 2.5, "tags": {"power": "pole"}},
        {"type": "way", "id": 2, "geometry": square, "tags": {"building": "yes"}},
        {"type": "way", "id": 3, "geometry": square[:3], "tags": {"highway": "footway"}},
        {"type": "relation", "id": 4, "tags": {"type": "multipolygon", "landuse": "grass"}, "members": [
            {"type": "way", "role": "outer", "geometry": square[:3]},
            {"type": "way", "role": "outer", "geometry": square[2:]},
            {"type": "way", "role": "inner", "geometry": [{"lat": .2, "lon": .2}, {"lat": .2, "lon": .4},
                                                          {"lat": .4, "lon": .4}, {"lat": .2, "lon": .2}]}]},
    ]}
    fc = osm.to_geojson(response)
    kinds = {f["properties"]["@id"]: f["geometry"]["type"] for f in fc["features"]}
    assert kinds == {"node/1": "Point", "way/2": "Polygon", "way/3": "LineString", "relation/4": "MultiPolygon"}
    relation = fc["features"][3]["geometry"]["coordinates"]
    assert len(relation) == 1 and len(relation[0]) == 2       # one polygon with one hole
