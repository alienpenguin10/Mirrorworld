mirrorworld.satellite: Satellite imagery (STAC)
===============================================

Imagery from STAC catalogues, read from cloud-optimized GeoTIFFs for just the requested box. Searching is
sync and async; reading uses GDAL and is sync only. Needs ``pip install mirrorworld[raster]``.
Scenes default to the newest acquisition covering the box; Sentinel-2 and Landsat additionally check the cloud
mask inside the box itself (``max_local_cloud``).

Generic STAC
------------
    .. autofunction:: mirrorworld.satellite.stac.search
    .. autofunction:: mirrorworld.satellite.stac.search_async
    .. autofunction:: mirrorworld.satellite.stac.read
    .. autofunction:: mirrorworld.satellite.stac.pick_scenes
    .. autofunction:: mirrorworld.satellite.stac.pick_clear_scenes
    .. autofunction:: mirrorworld.satellite.stac.sign_href

    Usage sample::

      from mirrorworld.satellite import stac

      scenes = stac.search(stac.PLANETARY_COMPUTER, "io-lulc-annual-v02", 47.615, -122.345, 47.600, -122.325)
      raster = stac.read(scenes[0], ["data"], 47.615, -122.345, 47.600, -122.325)

    .. autoclass:: mirrorworld.satellite.scene.Scene
      :members:

Sentinel-2 (10 m multispectral)
-------------------------------
    .. autofunction:: mirrorworld.satellite.sentinel2.find_scenes
    .. autofunction:: mirrorworld.satellite.sentinel2.find_scenes_async
    .. autofunction:: mirrorworld.satellite.sentinel2.get_raster
    .. autofunction:: mirrorworld.satellite.sentinel2.download_raster

    Usage sample::

      from mirrorworld.satellite import sentinel2

      r = sentinel2.get_raster(47.615, -122.345, 47.600, -122.325, bands=("red", "nir"),
                               start="2025-06-01", end="2025-09-30")
      red, nir = (r.band(b) * 0.0001 - 0.1 for b in ("red", "nir"))   # scale/offset from r.metadata["band_info"]
      ndvi = (nir - red) / (nir + red)


Sentinel-1 (10 m radar)
-----------------------
    .. autofunction:: mirrorworld.satellite.sentinel1.find_scenes
    .. autofunction:: mirrorworld.satellite.sentinel1.find_scenes_async
    .. autofunction:: mirrorworld.satellite.sentinel1.get_raster
    .. autofunction:: mirrorworld.satellite.sentinel1.download_raster

    Usage sample::

      from mirrorworld.satellite import sentinel1

      sentinel1.download_raster(47.615, -122.345, 47.600, -122.325, "s1.tif", start="2025-07-01", end="2025-07-31")


Landsat (30 m multispectral and thermal)
----------------------------------------
    .. autofunction:: mirrorworld.satellite.landsat.find_scenes
    .. autofunction:: mirrorworld.satellite.landsat.find_scenes_async
    .. autofunction:: mirrorworld.satellite.landsat.get_raster
    .. autofunction:: mirrorworld.satellite.landsat.download_raster

    Usage sample::

      from mirrorworld.satellite import landsat

      landsat.download_raster(47.615, -122.345, 47.600, -122.325, "lst.tif", bands=("lwir11",),
                              start="2025-06-01", end="2025-09-30")


NAIP (0.6 m RGB + near-infrared, US)
------------------------------------
    .. autofunction:: mirrorworld.satellite.naip.find_scenes
    .. autofunction:: mirrorworld.satellite.naip.find_scenes_async
    .. autofunction:: mirrorworld.satellite.naip.get_raster
    .. autofunction:: mirrorworld.satellite.naip.download_raster

    Usage sample::

      from mirrorworld.satellite import naip

      naip.download_raster(47.615, -122.345, 47.600, -122.325, "naip.tif")


ESA WorldCover (10 m land cover)
--------------------------------
    .. autofunction:: mirrorworld.satellite.worldcover.find_scenes
    .. autofunction:: mirrorworld.satellite.worldcover.find_scenes_async
    .. autofunction:: mirrorworld.satellite.worldcover.get_raster
    .. autofunction:: mirrorworld.satellite.worldcover.download_raster

    Usage sample::

      from mirrorworld.satellite import worldcover

      r = worldcover.get_raster(47.615, -122.345, 47.600, -122.325)
      print(worldcover.CLASSES)
