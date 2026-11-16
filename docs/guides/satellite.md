# Satellite imagery

Search a STAC catalogue, then read **only your box** straight from cloud-optimized GeoTIFFs — no scene downloads.

```{figure} ../_static/teasers/sentinel2_ndvi.jpg
:class: mw-figure
:alt: NDVI map of Seattle

Summer 2025 NDVI over Seattle from Sentinel-2, computed in five lines. Contains modified Copernicus Sentinel data.
```

## Presets

| Module | What | Resolution | Coverage |
|---|---|---|---|
| `sentinel2` | multispectral surface reflectance, 13 bands | 10–60 m | worldwide, ~5-day revisit |
| `sentinel1` | radar backscatter (VV, VH), sees through cloud | 10 m | worldwide |
| `landsat` | multispectral + thermal (surface temperature) | 30 m | worldwide, since 1982 |
| `naip` | aerial RGB + near-infrared | 0.6 m | contiguous US |
| `worldcover` | land cover classes | 10 m | worldwide |

All of them share `find_scenes`, `get_raster` and `download_raster`:

```python
from mirrorworld.satellite import sentinel2

r = sentinel2.get_raster(47.640, -122.360, 47.595, -122.290, bands=("red", "nir"),
                         start="2025-06-01", end="2025-09-30")
scale = r.metadata["band_info"]["red"]          # e.g. {'scale': 0.0001, 'offset': 0.0}
red, nir = (r.band(b) * scale["scale"] + scale["offset"] for b in ("red", "nir"))
ndvi = (nir - red) / (nir + red)
```

:::{admonition} Clouds, handled locally
:class: tip
A scene can be 5% cloudy overall and 100% cloudy over your street. For Sentinel-2 and Landsat, `get_raster` reads the
mission's cloud mask **inside your box** and picks the newest scene that is clear there (`max_local_cloud=0.1`).
:::

```{figure} ../_static/teasers/naip_false_color.jpg
:class: mw-figure
:alt: NAIP false colour

NAIP at 0.6 m in false colour (near-infrared, red, green): trees and parks in red. USDA NAIP, public domain.
```

## Any STAC collection

```python
from mirrorworld.satellite import stac

scenes = stac.search(stac.PLANETARY_COMPUTER, "io-lulc-annual-v02", 47.615, -122.345, 47.600, -122.325)
raster = stac.read(scenes[0], ["data"], 47.615, -122.345, 47.600, -122.325)
```

Planetary Computer assets are signed anonymously behind the scenes. Reading uses GDAL and is synchronous; searching
has async twins.

**API:** {doc}`../reference/mirrorworld.satellite`
