# Mirrorworld addition (not in upstream streetlevel).
"""
Generic clients for standard map services, so that any public WMS, WMTS, WCS or ArcGIS server can be used:
national orthophotos, elevation models, land-cover maps and more. Each returns a :class:`streetlevel.raster.Raster`
for a WGS84 bounding box.

Usage::

    from streetlevel.services import wms

    raster = wms.get_raster("https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0", "Actueel_orthoHR",
                            52.3735, 4.8910, 52.3725, 4.8930, resolution=0.08, crs="EPSG:28992")
    raster.save("dam.png")
"""
