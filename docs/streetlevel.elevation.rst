streetlevel.elevation: Elevation models
=======================================

Elevation for a bounding box (Netherlands, England, Wales, United States, worldwide) as :class:`streetlevel.raster.Raster` objects in meters. Needs
``pip install streetlevel[raster]``.

AHN (Netherlands, 0.5 m)
------------------------
    .. autofunction:: streetlevel.elevation.ahn.get_dsm
    .. autofunction:: streetlevel.elevation.ahn.get_dsm_async
    .. autofunction:: streetlevel.elevation.ahn.get_dtm
    .. autofunction:: streetlevel.elevation.ahn.get_dtm_async
    .. autofunction:: streetlevel.elevation.ahn.get_ndsm
    .. autofunction:: streetlevel.elevation.ahn.get_ndsm_async
    .. autofunction:: streetlevel.elevation.ahn.download_dsm
    .. autofunction:: streetlevel.elevation.ahn.download_dtm
    .. autofunction:: streetlevel.elevation.ahn.download_ndsm
    .. autofunction:: streetlevel.elevation.ahn.compute_ndsm

    Usage sample::

      from streetlevel.elevation import ahn

      heights = ahn.get_ndsm(52.3736, 4.8915, 52.3728, 4.8932)   # object heights above ground
      heights.save("ndsm.tif")


Environment Agency (England, 1 m)
---------------------------------
    .. autofunction:: streetlevel.elevation.ea.get_dtm
    .. autofunction:: streetlevel.elevation.ea.get_dtm_async
    .. autofunction:: streetlevel.elevation.ea.get_dsm
    .. autofunction:: streetlevel.elevation.ea.get_dsm_async
    .. autofunction:: streetlevel.elevation.ea.get_ndsm
    .. autofunction:: streetlevel.elevation.ea.get_ndsm_async
    .. autofunction:: streetlevel.elevation.ea.download_dtm
    .. autofunction:: streetlevel.elevation.ea.download_dsm
    .. autofunction:: streetlevel.elevation.ea.download_ndsm

    Usage sample::

      from streetlevel.elevation import ea

      heights = ea.get_ndsm(51.50785, -0.1287, 51.50695, -0.1269)   # object heights, Charing Cross
      heights.save("ndsm.tif")

Wales (1 m)
-----------
    .. autofunction:: streetlevel.elevation.wales.get_dsm
    .. autofunction:: streetlevel.elevation.wales.get_dtm
    .. autofunction:: streetlevel.elevation.wales.get_ndsm
    .. autofunction:: streetlevel.elevation.wales.download_dsm
    .. autofunction:: streetlevel.elevation.wales.download_dtm
    .. autofunction:: streetlevel.elevation.wales.download_ndsm

    Usage sample::

      from streetlevel.elevation import wales

      wales.download_dsm(51.4820, -3.1830, 51.4800, -3.1780, "cardiff_dsm.tif")

USGS 3DEP (United States, bare earth)
-------------------------------------
    .. autofunction:: streetlevel.elevation.usgs3dep.get_dem
    .. autofunction:: streetlevel.elevation.usgs3dep.get_dem_async
    .. autofunction:: streetlevel.elevation.usgs3dep.download_dem

    Usage sample::

      from streetlevel.elevation import usgs3dep

      usgs3dep.download_dem(47.6068, -122.3340, 47.6058, -122.3325, "dem.tif", resolution=1.0)


Copernicus DEM (worldwide, 30 m surface model)
----------------------------------------------
    .. autofunction:: streetlevel.elevation.copernicus.find_scenes
    .. autofunction:: streetlevel.elevation.copernicus.find_scenes_async
    .. autofunction:: streetlevel.elevation.copernicus.get_raster
    .. autofunction:: streetlevel.elevation.copernicus.download_raster

    Usage sample::

      from streetlevel.elevation import copernicus

      copernicus.download_raster(47.615, -122.345, 47.600, -122.325, "cop30.tif")
