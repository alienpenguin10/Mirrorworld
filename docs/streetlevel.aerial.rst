streetlevel.aerial: Aerial imagery
==================================

Orthoimagery from web map tile services, stitched for a bounding box and saved with its georeferencing
(EPSG:3857). Every provider has the same functions; replace ``bing`` with ``google``, ``esri`` or ``usgs``.

    Usage sample::

      from streetlevel.aerial import bing

      print(bing.find_max_zoom(47.6062, -122.3321))  # 20, i.e. 0.10 m/px
      aerial = bing.download_image(47.6070, -122.3345, 47.6055, -122.3320, "seattle.jpg", zoom=20)
      print(aerial.ground_resolution, aerial.metadata)

    Command line::

      python -m streetlevel.aerial bing 47.6070 -122.3345 47.6055 -122.3320 seattle.jpg --resolution 0.10
      python -m streetlevel.aerial esri 47.6070 -122.3345 47.6055 -122.3320 --max-zoom

Bing Maps
---------
    .. autofunction:: streetlevel.aerial.bing.find_max_zoom
    .. autofunction:: streetlevel.aerial.bing.find_max_zoom_async
    .. autofunction:: streetlevel.aerial.bing.get_image
    .. autofunction:: streetlevel.aerial.bing.get_image_async
    .. autofunction:: streetlevel.aerial.bing.download_image
    .. autofunction:: streetlevel.aerial.bing.download_image_async
    .. autofunction:: streetlevel.aerial.bing.get_tile
    .. autofunction:: streetlevel.aerial.bing.get_tile_async
    .. autofunction:: streetlevel.aerial.bing.build_permalink
    .. autofunction:: streetlevel.aerial.bing.to_quadkey
    .. autofunction:: streetlevel.aerial.bing.from_quadkey

Google Maps
-----------
    .. autofunction:: streetlevel.aerial.google.find_max_zoom
    .. autofunction:: streetlevel.aerial.google.find_max_zoom_async
    .. autofunction:: streetlevel.aerial.google.get_image
    .. autofunction:: streetlevel.aerial.google.get_image_async
    .. autofunction:: streetlevel.aerial.google.download_image
    .. autofunction:: streetlevel.aerial.google.download_image_async
    .. autofunction:: streetlevel.aerial.google.get_tile
    .. autofunction:: streetlevel.aerial.google.get_tile_async
    .. autofunction:: streetlevel.aerial.google.build_permalink

Esri World Imagery
------------------
    .. autofunction:: streetlevel.aerial.esri.find_max_zoom
    .. autofunction:: streetlevel.aerial.esri.find_max_zoom_async
    .. autofunction:: streetlevel.aerial.esri.get_image
    .. autofunction:: streetlevel.aerial.esri.get_image_async
    .. autofunction:: streetlevel.aerial.esri.download_image
    .. autofunction:: streetlevel.aerial.esri.download_image_async
    .. autofunction:: streetlevel.aerial.esri.get_tile
    .. autofunction:: streetlevel.aerial.esri.get_tile_async
    .. autofunction:: streetlevel.aerial.esri.build_permalink

USGS The National Map
---------------------
    .. autofunction:: streetlevel.aerial.usgs.find_max_zoom
    .. autofunction:: streetlevel.aerial.usgs.find_max_zoom_async
    .. autofunction:: streetlevel.aerial.usgs.get_image
    .. autofunction:: streetlevel.aerial.usgs.get_image_async
    .. autofunction:: streetlevel.aerial.usgs.download_image
    .. autofunction:: streetlevel.aerial.usgs.download_image_async
    .. autofunction:: streetlevel.aerial.usgs.get_tile
    .. autofunction:: streetlevel.aerial.usgs.get_tile_async

Data classes and utilities
--------------------------
    .. autoclass:: streetlevel.aerial.dataclasses.AerialImage
      :members:
    .. autofunction:: streetlevel.aerial.util.save_aerial_image
    .. autofunction:: streetlevel.aerial.util.ground_resolution
    .. autofunction:: streetlevel.aerial.util.zoom_for_resolution
