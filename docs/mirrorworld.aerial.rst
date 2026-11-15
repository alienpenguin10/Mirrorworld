mirrorworld.aerial: Aerial imagery
==================================

Orthoimagery from web map tile services, stitched for a bounding box and saved with its georeferencing
(EPSG:3857). Every provider has the same functions; replace ``bing`` with ``google``, ``esri`` or ``usgs``.

    Usage sample::

      from mirrorworld.aerial import bing

      print(bing.find_max_zoom(47.6062, -122.3321))  # 20, i.e. 0.10 m/px
      aerial = bing.download_image(47.6070, -122.3345, 47.6055, -122.3320, "seattle.jpg", zoom=20)
      print(aerial.ground_resolution, aerial.metadata)

    Command line::

      python -m mirrorworld.aerial bing 47.6070 -122.3345 47.6055 -122.3320 seattle.jpg --resolution 0.10
      python -m mirrorworld.aerial esri 47.6070 -122.3345 47.6055 -122.3320 --max-zoom

Bing Maps
---------
    .. autofunction:: mirrorworld.aerial.bing.find_max_zoom
    .. autofunction:: mirrorworld.aerial.bing.find_max_zoom_async
    .. autofunction:: mirrorworld.aerial.bing.get_image
    .. autofunction:: mirrorworld.aerial.bing.get_image_async
    .. autofunction:: mirrorworld.aerial.bing.download_image
    .. autofunction:: mirrorworld.aerial.bing.download_image_async
    .. autofunction:: mirrorworld.aerial.bing.get_tile
    .. autofunction:: mirrorworld.aerial.bing.get_tile_async
    .. autofunction:: mirrorworld.aerial.bing.build_permalink
    .. autofunction:: mirrorworld.aerial.bing.to_quadkey
    .. autofunction:: mirrorworld.aerial.bing.from_quadkey

Google Maps
-----------
    .. autofunction:: mirrorworld.aerial.google.find_max_zoom
    .. autofunction:: mirrorworld.aerial.google.find_max_zoom_async
    .. autofunction:: mirrorworld.aerial.google.get_image
    .. autofunction:: mirrorworld.aerial.google.get_image_async
    .. autofunction:: mirrorworld.aerial.google.download_image
    .. autofunction:: mirrorworld.aerial.google.download_image_async
    .. autofunction:: mirrorworld.aerial.google.get_tile
    .. autofunction:: mirrorworld.aerial.google.get_tile_async
    .. autofunction:: mirrorworld.aerial.google.build_permalink

Esri World Imagery
------------------
    .. autofunction:: mirrorworld.aerial.esri.find_max_zoom
    .. autofunction:: mirrorworld.aerial.esri.find_max_zoom_async
    .. autofunction:: mirrorworld.aerial.esri.get_image
    .. autofunction:: mirrorworld.aerial.esri.get_image_async
    .. autofunction:: mirrorworld.aerial.esri.download_image
    .. autofunction:: mirrorworld.aerial.esri.download_image_async
    .. autofunction:: mirrorworld.aerial.esri.get_tile
    .. autofunction:: mirrorworld.aerial.esri.get_tile_async
    .. autofunction:: mirrorworld.aerial.esri.build_permalink

USGS The National Map
---------------------
    .. autofunction:: mirrorworld.aerial.usgs.find_max_zoom
    .. autofunction:: mirrorworld.aerial.usgs.find_max_zoom_async
    .. autofunction:: mirrorworld.aerial.usgs.get_image
    .. autofunction:: mirrorworld.aerial.usgs.get_image_async
    .. autofunction:: mirrorworld.aerial.usgs.download_image
    .. autofunction:: mirrorworld.aerial.usgs.download_image_async
    .. autofunction:: mirrorworld.aerial.usgs.get_tile
    .. autofunction:: mirrorworld.aerial.usgs.get_tile_async

Esri World Imagery Wayback
--------------------------
Every archived release of Esri World Imagery since 2014, for change detection and multi-temporal work.
:func:`find_versions` lists only the releases that changed the imagery at a place, with capture dates.

    .. autofunction:: mirrorworld.aerial.wayback.get_releases
    .. autofunction:: mirrorworld.aerial.wayback.get_releases_async
    .. autofunction:: mirrorworld.aerial.wayback.find_versions
    .. autofunction:: mirrorworld.aerial.wayback.find_versions_async
    .. autofunction:: mirrorworld.aerial.wayback.get_image
    .. autofunction:: mirrorworld.aerial.wayback.get_image_async
    .. autofunction:: mirrorworld.aerial.wayback.download_image
    .. autofunction:: mirrorworld.aerial.wayback.download_image_async
    .. autofunction:: mirrorworld.aerial.wayback.merge_versions

    Usage sample::

      from mirrorworld.aerial import wayback

      versions = wayback.find_versions(47.6062, -122.3321)
      for v in versions:
          print(v.release.date, v.capture_date, v.resolution, v.provider)
      wayback.download_image(47.6068, -122.3340, 47.6058, -122.3325, "2011.jpg", release=versions[-1])

    .. autoclass:: mirrorworld.aerial.wayback.release.WaybackRelease
      :members:
    .. autoclass:: mirrorworld.aerial.wayback.release.WaybackVersion
      :members:

PDOK (Netherlands)
------------------
Yearly nationwide Dutch orthophotos in RGB and colour-infrared at 8 cm (5 cm in parts of 2025-2026) and 25 cm.
Returns a :class:`mirrorworld.raster.Raster`.

    .. autofunction:: mirrorworld.aerial.pdok.get_raster
    .. autofunction:: mirrorworld.aerial.pdok.get_raster_async
    .. autofunction:: mirrorworld.aerial.pdok.download_raster
    .. autofunction:: mirrorworld.aerial.pdok.list_layers
    .. autofunction:: mirrorworld.aerial.pdok.layer_name

    Usage sample::

      from mirrorworld.aerial import pdok

      pdok.download_raster(52.3736, 4.8915, 52.3728, 4.8932, "dam_2025_cir.png", year=2025, infrared=True)

Data classes and utilities
--------------------------
    .. autoclass:: mirrorworld.aerial.dataclasses.AerialImage
      :members:
    .. autofunction:: mirrorworld.aerial.util.save_aerial_image
    .. autofunction:: mirrorworld.aerial.util.ground_resolution
    .. autofunction:: mirrorworld.aerial.util.zoom_for_resolution
