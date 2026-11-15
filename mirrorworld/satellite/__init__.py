# Mirrorworld addition (not in upstream streetlevel).
"""
Satellite and aerial imagery from STAC catalogues, read straight from cloud-optimized GeoTIFFs for just the
requested bounding box (no full-scene downloads). Presets: ``sentinel2`` (10 m multispectral, worldwide),
``sentinel1`` (10 m radar, sees through cloud), ``landsat`` (30 m multispectral + thermal), ``naip``
(0.6 m RGB + near-infrared, United States) and ``worldcover`` (10 m land cover); :mod:`mirrorworld.satellite.stac`
works with any other STAC collection. Reading needs ``rasterio``.
"""
