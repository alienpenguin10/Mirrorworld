# Any map service

National mapping agencies, cities and research institutes publish data through a few standards. mirrorworld speaks
all of them, so a new data source is usually **one line**.

| Client | Standard | Returns |
|---|---|---|
| `services.wms` | OGC WMS 1.1.1 / 1.3.0 | rendered images (or GeoTIFF where offered) |
| `services.wmts` | OGC WMTS 1.0 (projected tile sets) | stitched tiles on their native grid |
| `services.wcs` | OGC WCS 2.0.1 | data values at native resolution |
| `services.arcgis` | ArcGIS ImageServer / MapServer | values or rendered images |
| `raster.read_cog` | cloud-optimized GeoTIFF over HTTP | values, only the bytes you need |

```python
from mirrorworld.services import wms, wcs
from mirrorworld.raster import read_cog

url = "https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0"
print([layer.name for layer in wms.get_layers(url)])
photo = wms.get_raster(url, "Actueel_orthoHR", 52.37365, 4.8912, 52.37275, 4.8935,
                       resolution=0.08, crs="EPSG:28992")

dsm = wcs.get_raster("https://service.pdok.nl/rws/ahn/wcs/v1_0", "dsm_05m",
                     52.37365, 4.8912, 52.37275, 4.8935)

wales = read_cog("https://dmwproductionblob.blob.core.windows.net/cogs/lidar/wales_dsm_32bit_cog.tif",
                 51.4820, -3.1830, 51.4800, -3.1780)
```

Large boxes are requested in chunks and mosaicked; stalled or failing requests are retried. Each client returns a
{class}`~mirrorworld.raster.Raster`.

:::{tip}
Found a useful service? Most of mirrorworld's presets (`pdok`, `ahn`, `ea`, `wales`, `usgs3dep`) are a dozen lines
around these clients — contributions welcome.
:::

**API:** {doc}`../reference/mirrorworld.services` · {doc}`../reference/raster`
