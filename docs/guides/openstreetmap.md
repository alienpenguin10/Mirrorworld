# OpenStreetMap

```{figure} ../_static/teasers/amsterdam_osm.jpg
:class: mw-figure
:alt: OSM features over an aerial photo

Buildings (orange), footways (green) and tram lines (blue) from `osm.find_features`, drawn on the 8 cm PDOK photo.
(c) OpenStreetMap contributors, ODbL; PDOK, CC BY 4.0.
```

Query any tags in a box through the Overpass API and get GeoJSON back:

```python
from mirrorworld.vector import osm

assets = osm.find_features(51.5079, -0.1287, 51.5070, -0.1269,
                           {"man_made": "street_cabinet", "power": ["pole", "tower"], "telecom": True})
sidewalks = osm.find_features(51.5079, -0.1287, 51.5070, -0.1269, ['["footway"="sidewalk"]["surface"]'])
osm.download_features(51.5079, -0.1287, 51.5070, -0.1269, {"building": True}, "buildings.geojson")
```

Filters are a dict (`True` = any value, a string = exact, a list = any of) or raw Overpass filter strings. Nodes
become Points, ways LineStrings or Polygons, multipolygon relations MultiPolygons; every feature keeps its tags and
`@id`.

:::{note}
Tag completeness varies a lot: sidewalks are widely mapped, street cabinets and poles much less (almost none around
our London test sites). Combine with [Mapillary map features](street-assets.md) for assets.
:::

**API:** {doc}`../reference/mirrorworld.vector`
