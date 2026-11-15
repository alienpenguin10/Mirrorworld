streetlevel.vector: OpenStreetMap features
==========================================

OpenStreetMap features through the Overpass API as GeoJSON (ODbL). Keep requests modest, or set ``endpoint``
to your own Overpass instance.

OpenStreetMap
-------------
    .. autofunction:: streetlevel.vector.osm.find_features
    .. autofunction:: streetlevel.vector.osm.find_features_async
    .. autofunction:: streetlevel.vector.osm.query
    .. autofunction:: streetlevel.vector.osm.query_async
    .. autofunction:: streetlevel.vector.osm.download_features
    .. autofunction:: streetlevel.vector.osm.build_query
    .. autofunction:: streetlevel.vector.osm.to_geojson

    Usage sample::

      from streetlevel.vector import osm

      assets = osm.find_features(47.61, -122.34, 47.60, -122.33,
                                 {"man_made": "street_cabinet", "power": ["pole", "tower"]})
      sidewalks = osm.find_features(47.61, -122.34, 47.60, -122.33, ['["footway"="sidewalk"]'])
      osm.download_features(47.61, -122.34, 47.60, -122.33, {"building": True}, "buildings.geojson")
