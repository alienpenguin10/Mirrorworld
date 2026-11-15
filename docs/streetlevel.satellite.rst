streetlevel.satellite: Satellite imagery (STAC)
===============================================

Imagery from STAC catalogues, read from cloud-optimized GeoTIFFs for just the requested box. Searching is
sync and async; reading uses GDAL and is sync only. Needs ``pip install streetlevel[raster]``.
Scenes default to the newest acquisition covering the box; Sentinel-2 and Landsat additionally check the cloud
mask inside the box itself (``max_local_cloud``).

Generic STAC
------------
    .. autofunction:: streetlevel.satellite.stac.search
    .. autofunction:: streetlevel.satellite.stac.search_async
    .. autofunction:: streetlevel.satellite.stac.read
    .. autofunction:: streetlevel.satellite.stac.pick_scenes
    .. autofunction:: streetlevel.satellite.stac.pick_clear_scenes
    .. autofunction:: streetlevel.satellite.stac.sign_href

    Usage sample::

      from streetlevel.satellite import stac

      scenes = stac.search(stac.PLANETARY_COMPUTER, "io-lulc-annual-v02", 47.615, -122.345, 47.600, -122.325)
      raster = stac.read(scenes[0], ["data"], 47.615, -122.345, 47.600, -122.325)

    .. autoclass:: streetlevel.satellite.scene.Scene
      :members:

Sentinel-2 (10 m multispectral)
-------------------------------
    .. autofunction:: streetlevel.satellite.sentinel2.find_scenes
    .. autofunction:: streetlevel.satellite.sentinel2.find_scenes_async
    .. autofunction:: streetlevel.satellite.sentinel2.get_raster
    .. autofunction:: streetlevel.satellite.sentinel2.download_raster

    Usage sample::

      from streetlevel.satellite import sentinel2

      r = sentinel2.get_raster(47.615, -122.345, 47.600, -122.325, bands=("red", "nir"),
                               start="2025-06-01", end="2025-09-30")
      red, nir = (r.band(b) * 0.0001 - 0.1 for b in ("red", "nir"))   # scale/offset from r.metadata["band_info"]
      ndvi = (nir - red) / (nir + red)


Sentinel-1 (10 m radar)
-----------------------
    .. autofunction:: streetlevel.satellite.sentinel1.find_scenes
    .. autofunction:: streetlevel.satellite.sentinel1.find_scenes_async
    .. autofunction:: streetlevel.satellite.sentinel1.get_raster
    .. autofunction:: streetlevel.satellite.sentinel1.download_raster

    Usage sample::

      from streetlevel.satellite import sentinel1

      sentinel1.download_raster(47.615, -122.345, 47.600, -122.325, "s1.tif", start="2025-07-01", end="2025-07-31")


Landsat (30 m multispectral and thermal)
----------------------------------------
    .. autofunction:: streetlevel.satellite.landsat.find_scenes
    .. autofunction:: streetlevel.satellite.landsat.find_scenes_async
    .. autofunction:: streetlevel.satellite.landsat.get_raster
    .. autofunction:: streetlevel.satellite.landsat.download_raster

    Usage sample::

      from streetlevel.satellite import landsat

      landsat.download_raster(47.615, -122.345, 47.600, -122.325, "lst.tif", bands=("lwir11",),
                              start="2025-06-01", end="2025-09-30")


NAIP (0.6 m RGB + near-infrared, US)
------------------------------------
    .. autofunction:: streetlevel.satellite.naip.find_scenes
    .. autofunction:: streetlevel.satellite.naip.find_scenes_async
    .. autofunction:: streetlevel.satellite.naip.get_raster
    .. autofunction:: streetlevel.satellite.naip.download_raster

    Usage sample::

      from streetlevel.satellite import naip

      naip.download_raster(47.615, -122.345, 47.600, -122.325, "naip.tif")


ESA WorldCover (10 m land cover)
--------------------------------
    .. autofunction:: streetlevel.satellite.worldcover.find_scenes
    .. autofunction:: streetlevel.satellite.worldcover.find_scenes_async
    .. autofunction:: streetlevel.satellite.worldcover.get_raster
    .. autofunction:: streetlevel.satellite.worldcover.download_raster

    Usage sample::

      from streetlevel.satellite import worldcover

      r = worldcover.get_raster(47.615, -122.345, 47.600, -122.325)
      print(worldcover.CLASSES)
