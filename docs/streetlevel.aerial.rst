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

Esri World Imagery Wayback
--------------------------
Every archived release of Esri World Imagery since 2014, for change detection and multi-temporal work.
:func:`find_versions` lists only the releases that changed the imagery at a place, with capture dates.

    .. autofunction:: streetlevel.aerial.wayback.get_releases
    .. autofunction:: streetlevel.aerial.wayback.get_releases_async
    .. autofunction:: streetlevel.aerial.wayback.find_versions
    .. autofunction:: streetlevel.aerial.wayback.find_versions_async
    .. autofunction:: streetlevel.aerial.wayback.get_image
    .. autofunction:: streetlevel.aerial.wayback.get_image_async
    .. autofunction:: streetlevel.aerial.wayback.download_image
    .. autofunction:: streetlevel.aerial.wayback.download_image_async
    .. autofunction:: streetlevel.aerial.wayback.merge_versions

    Usage sample::

      from streetlevel.aerial import wayback

      versions = wayback.find_versions(47.6062, -122.3321)
      for v in versions:
          print(v.release.date, v.capture_date, v.resolution, v.provider)
      wayback.download_image(47.6068, -122.3340, 47.6058, -122.3325, "2011.jpg", release=versions[-1])

    .. autoclass:: streetlevel.aerial.wayback.release.WaybackRelease
      :members:
    .. autoclass:: streetlevel.aerial.wayback.release.WaybackVersion
      :members:

PDOK (Netherlands)
------------------
Yearly nationwide Dutch orthophotos in RGB and colour-infrared at 8 cm (5 cm in parts of 2025-2026) and 25 cm.
Returns a :class:`streetlevel.raster.Raster`.

    .. autofunction:: streetlevel.aerial.pdok.get_raster
    .. autofunction:: streetlevel.aerial.pdok.get_raster_async
    .. autofunction:: streetlevel.aerial.pdok.download_raster
    .. autofunction:: streetlevel.aerial.pdok.list_layers
    .. autofunction:: streetlevel.aerial.pdok.layer_name

    Usage sample::

      from streetlevel.aerial import pdok

      pdok.download_raster(52.3736, 4.8915, 52.3728, 4.8932, "dam_2025_cir.png", year=2025, infrared=True)

Data classes and utilities
--------------------------
    .. autoclass:: streetlevel.aerial.dataclasses.AerialImage
      :members:
    .. autofunction:: streetlevel.aerial.util.save_aerial_image
    .. autofunction:: streetlevel.aerial.util.ground_resolution
    .. autofunction:: streetlevel.aerial.util.zoom_for_resolution
