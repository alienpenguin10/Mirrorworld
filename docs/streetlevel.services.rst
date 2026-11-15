streetlevel.services: Generic map services
==========================================

Clients for any public OGC WMS, WMTS, WCS or ArcGIS REST server (national orthophotos, elevation, land cover,
...). Each takes a WGS84 bounding box and returns a :class:`streetlevel.raster.Raster`; large areas are requested
in chunks. GeoTIFF responses (WCS, ArcGIS ``tiff``) need ``pip install streetlevel[raster]``.

WMS
---
    .. autofunction:: streetlevel.services.wms.get_layers
    .. autofunction:: streetlevel.services.wms.get_layers_async
    .. autofunction:: streetlevel.services.wms.get_raster
    .. autofunction:: streetlevel.services.wms.get_raster_async
    .. autofunction:: streetlevel.services.wms.download_raster

    Usage sample::

      from streetlevel.services import wms

      url = "https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0"
      print([layer.name for layer in wms.get_layers(url)])
      wms.download_raster(url, "Actueel_orthoHR", 52.3736, 4.8915, 52.3728, 4.8932, "dam.png",
                          resolution=0.08, crs="EPSG:28992")


WMTS
----
    .. autofunction:: streetlevel.services.wmts.get_capabilities
    .. autofunction:: streetlevel.services.wmts.get_capabilities_async
    .. autofunction:: streetlevel.services.wmts.get_raster
    .. autofunction:: streetlevel.services.wmts.get_raster_async
    .. autofunction:: streetlevel.services.wmts.download_raster

    Usage sample::

      from streetlevel.services import wmts

      wmts.download_raster("https://service.pdok.nl/hwh/luchtfotorgb/wmts/v1_0", "Actueel_orthoHR",
                           52.3736, 4.8915, 52.3728, 4.8932, "dam.jpg", resolution=0.08, crs="EPSG:28992")


WCS
---
    .. autofunction:: streetlevel.services.wcs.get_coverage_ids
    .. autofunction:: streetlevel.services.wcs.get_coverage_ids_async
    .. autofunction:: streetlevel.services.wcs.describe_coverage
    .. autofunction:: streetlevel.services.wcs.describe_coverage_async
    .. autofunction:: streetlevel.services.wcs.get_raster
    .. autofunction:: streetlevel.services.wcs.get_raster_async
    .. autofunction:: streetlevel.services.wcs.download_raster

    Usage sample::

      from streetlevel.services import wcs

      wcs.download_raster("https://service.pdok.nl/rws/ahn/wcs/v1_0", "dsm_05m",
                          52.3736, 4.8915, 52.3728, 4.8932, "dsm.tif")


ArcGIS
------
    .. autofunction:: streetlevel.services.arcgis.get_info
    .. autofunction:: streetlevel.services.arcgis.get_info_async
    .. autofunction:: streetlevel.services.arcgis.get_raster
    .. autofunction:: streetlevel.services.arcgis.get_raster_async
    .. autofunction:: streetlevel.services.arcgis.download_raster

    Usage sample::

      from streetlevel.services import arcgis

      arcgis.download_raster("https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer",
                             47.6068, -122.3340, 47.6058, -122.3325, "dem.tif", resolution=1.0,
                             crs="EPSG:32610", pixel_type="F32")
