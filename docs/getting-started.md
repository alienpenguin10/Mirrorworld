# Getting started

## Install

```bash
pip install mirrorworld            # street-level, aerial tiles, OpenStreetMap, map services
pip install "mirrorworld[all]"     # + satellite, elevation and GeoTIFF (rasterio) and LiDAR (laspy)
```

mirrorworld needs Python 3.10 or newer. macOS users may need `brew install gettext inih` for the Exif library
([details](https://github.com/LeoHsiao1/pyexiv2/blob/master/docs/Tutorial.md#faq)).

| Extra | Adds | Needed for |
|---|---|---|
| *(none)* | | street-level, aerial tiles, Wayback, PDOK, OpenStreetMap, WMS/WMTS PNG/JPEG |
| `raster` | rasterio | satellite, elevation, WCS and ArcGIS GeoTIFF, saving any raster as `.tif` |
| `lidar` | laspy + LAZ | LiDAR point clouds |
| `all` | both | everything |

## Keys and tokens

Almost nothing needs a key. The one exception is **Mapillary**, whose token is free:

1. Create one at <https://www.mapillary.com/dashboard/developers> (it looks like `MLY|...`).
2. Either export it once, or pass it to each call:

```bash
export MAPILLARY_ACCESS_TOKEN="MLY|..."
```

```python
from mirrorworld import mapillary

mapillary.find_panoramas(51.5074, -0.1278, access_token="MLY|...")
```

## Three conventions to know

**1. Latitude first.** Points are `(lat, lon)` and boxes are `(north, west, south, east)`, all WGS84 —
the same order you would read off a map. Unpacking a tuple keeps calls short:

```python
from mirrorworld.elevation import ea

box = (51.5079, -0.1287, 51.5070, -0.1269)   # Charing Cross, London
ea.get_ndsm(*box)
```

**2. Sync and async twins.** Network-bound functions come in pairs. The async one takes an `aiohttp.ClientSession`
as its first keyword argument after the location:

```python
pano = mapillary.find_panorama_by_id(1340409547112764)                   # sync
pano = await mapillary.find_panorama_by_id_async(1340409547112764, session)  # async
```

**3. Three result types.**

`Panorama` objects
: Street-level metadata (`id`, `lat`, `lon`, `date`, `heading` in radians, ...) from each provider's `find_*`
  functions; pass them to `get_panorama` / `download_panorama`.

{class}`~mirrorworld.raster.Raster`
: Any gridded result (satellite, elevation, map services, PDOK): a `(bands, rows, cols)` NumPy array with `crs`,
  `transform`, `nodata`, `band_names` and `metadata`. `raster.save("x.tif")` keeps every value;
  `raster.save("x.png")` writes an 8-bit rendering with a world file; `raster.to_image()` gives a PIL image.

{class}`~mirrorworld.aerial.dataclasses.AerialImage`
: Stitched web-map tiles (Bing, Google, Esri, USGS, Wayback) in Web Mercator, with `image`, bounds, resolution and
  capture metadata.

## Your first five minutes

```python
from mirrorworld import mapillary, panoramax
from mirrorworld.aerial import wayback
from mirrorworld.satellite import sentinel2

# 1. What street-level imagery exists here?
pics = mapillary.find_panoramas(51.5074, -0.1278, radius=30)
print(len(pics), "images; newest", max(p.date for p in pics))

# 2. Download the closest one with Exif/GPano metadata
mapillary.download_panorama(pics[0], "closest.jpg", size="2048")

# 3. How has this place changed from above?
for version in wayback.find_versions(51.5074, -0.1278):
    print(version.capture_date, version.resolution, "m", version.provider)

# 4. A cloud-free Sentinel-2 view of the block (scene chosen by the cloud mask inside your box)
s2 = sentinel2.get_raster(51.5079, -0.1287, 51.5070, -0.1269, bands=("red", "green", "blue", "nir"))
s2.to_image(["red", "green", "blue"]).save("s2.png")
```

:::{tip}
Every function has a docstring with parameters, defaults and units — `help(mirrorworld.elevation.ea.get_ndsm)` or
the [API reference](reference/index.md).
:::

## When things go wrong

`ValueError: ... covers the Netherlands only`
: You asked a regional dataset for a place outside it. The [coverage table](coverage.md) lists what works where.

`ImportError: This function needs rasterio`
: Install the extra: `pip install "mirrorworld[raster]"` (or `[lidar]` for point clouds).

Slow or failing requests
: Public services are sometimes busy. mirrorworld retries server errors and stalled requests with backoff; for bulk
  work, keep boxes small and loop, and respect each provider's terms.
