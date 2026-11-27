# mirrorworld

[![PyPI](https://img.shields.io/pypi/v/mirrorworld?color=6c5cff)](https://pypi.org/project/mirrorworld/) [![Docs](https://img.shields.io/badge/docs-online-2fc6e8)](https://alienpenguin10.github.io/Mirrorworld/) [![Tests](https://github.com/alienpenguin10/Mirrorworld/actions/workflows/python-test.yml/badge.svg)](https://github.com/alienpenguin10/Mirrorworld/actions/workflows/python-test.yml)

**mirrorworld** fetches data about a place from many sources with one consistent API: street-level imagery
(Google Street View, Apple Look Around, Mapillary, KartaView, Panoramax and more), detected street assets,
aerial and satellite imagery, elevation models, LiDAR point clouds, any OGC/ArcGIS map service and
OpenStreetMap features. Everything is downloaded on demand for a point or bounding box; nothing is hosted by
this project.

It is a fork of [streetlevel](https://github.com/sk-zk/streetlevel) by sk-zk, whose street-level providers use the
services' internal APIs: no API keys are required for them, but they may break unexpectedly.

(Nearly) all functions are available as either a sync function using `requests` or an async function
using `aiohttp`, requiring a `ClientSession`.

## Installation

```sh
pip install mirrorworld
pip install "mirrorworld[all]"   # plus GeoTIFF (rasterio) and LiDAR (laspy) support
```

The extras can also be installed separately: `mirrorworld[raster]` for satellite, elevation and GeoTIFF output,
`mirrorworld[lidar]` for point clouds.

macOS users may need to install [additional dependencies](https://github.com/LeoHsiao1/pyexiv2/blob/master/docs/Tutorial.md#faq):

```sh
brew install gettext
brew install inih
```

## Example
Downloading the closest Google Street View panorama to a specific location, sync:

```python
from mirrorworld import streetview

pano = streetview.find_panorama(46.883958, 12.169002)
streetview.download_panorama(pano, f"{pano.id}.jpg")
```

Or async:

```python
from mirrorworld import streetview
from aiohttp import ClientSession

async with ClientSession() as session:
    pano = await streetview.find_panorama_async(46.883958, 12.169002, session)
    await streetview.download_panorama_async(pano, f"{pano.id}.jpg", session)
```

## More modalities for a place
On top of streetlevel's providers, mirrorworld adds sources that researchers commonly need next to street-level panoramas. Everything is fetched on
demand for a point or a bounding box (WGS84, lat/lon order) and nothing is hosted by us; results carry their
georeferencing and source metadata. Sync and async variants are provided wherever the work is network-bound.

| Modality | Module | Sources | Coverage | Key |
|---|---|---|---|---|
| Open street-level imagery | `mapillary`, `kartaview`, `panoramax` | Mapillary, KartaView, Panoramax (all CC BY-SA) | worldwide, crowd-sourced: Mapillary dense in cities (incl. UK); KartaView and Panoramax patchy (Panoramax strongest in France) | Mapillary: free token |
| Detected street assets | `mapillary` (`find_map_features`, `get_detections`, `get_point_cloud`) | Mapillary map features (poles, manholes, junction boxes, signs, ...), segmentations, SfM point clouds | wherever Mapillary has imagery | free token |
| Aerial imagery (web tiles) | `aerial.bing`, `aerial.google`, `aerial.esri`, `aerial.usgs` | Bing, Google, Esri World Imagery, USGS | worldwide (USGS: US only) | none |
| Dated aerial imagery | `aerial.wayback` | Esri World Imagery Wayback, 2014 onwards | worldwide | none |
| National orthophotos | `aerial.pdok` | Netherlands RGB + colour-infrared, 8 cm | Netherlands | none |
| Satellite | `satellite.sentinel2`, `sentinel1`, `landsat`, `naip`, `worldcover`, generic `satellite.stac` | Earth Search, Microsoft Planetary Computer | worldwide (NAIP: US only) | none |
| Elevation | `elevation.ea`, `elevation.wales`, `elevation.ahn`, `elevation.usgs3dep`, `elevation.copernicus` | Environment Agency LiDAR (1 m), Welsh Government LiDAR (1 m), AHN (0.5 m), USGS 3DEP, Copernicus GLO-30 | England, Wales, Netherlands, US, worldwide (30 m) | none |
| LiDAR point clouds | `lidar.usgs3dep`, `lidar.ea`, generic `lidar.ept` | USGS 3DEP on AWS, Environment Agency National LIDAR Programme (OGL v3) | US, England (any EPT dataset elsewhere) | none |
| Any map service | `services.wms`, `wmts`, `wcs`, `arcgis`, `raster.read_cog` | any OGC / ArcGIS server or cloud-optimized GeoTIFF | depends on the service | depends |
| Vector map data | `vector.osm` | OpenStreetMap via Overpass (ODbL) | worldwide; tag completeness varies (UK street cabinets and poles are sparsely mapped) | none |

```python
from mirrorworld import mapillary, panoramax
from mirrorworld.aerial import wayback, pdok
from mirrorworld.satellite import sentinel2
from mirrorworld.elevation import ahn
from mirrorworld.lidar import usgs3dep
from mirrorworld.vector import osm

poles = mapillary.find_map_features(47.68, -122.30, radius=150, values=["object--support--utility-pole"])
pics = panoramax.find_panoramas(51.5088, -0.127, radius=30)
versions = wayback.find_versions(47.6062, -122.3321)            # dated imagery versions at a place
pdok.download_raster(52.3736, 4.8915, 52.3728, 4.8932, "dam_cir.png", infrared=True)
s2 = sentinel2.get_raster(47.615, -122.345, 47.600, -122.325, bands=("red", "nir"))
heights = ahn.get_ndsm(52.3736, 4.8915, 52.3728, 4.8932)         # object heights above ground
las = usgs3dep.get_points(47.6068, -122.3340, 47.6058, -122.3325, resolution=1.0)
cabinets = osm.find_features(47.61, -122.34, 47.60, -122.33, {"man_made": "street_cabinet"})
```

Optional dependencies: `pip install "mirrorworld[raster]"` (rasterio: GeoTIFF/COG for satellite, elevation, WCS,
ArcGIS) and `pip install "mirrorworld[lidar]"` (laspy with LAZ support). Mapillary reads its token from
`access_token=` or `MAPILLARY_ACCESS_TOKEN`.

Each source keeps its own terms (listed in each module's docstring and the docs). Bing and Google tiles use
unofficial endpoints; check their terms before relying on them.

## Documentation
**Documentation: <https://alienpenguin10.github.io/Mirrorworld/>** — guides, recipes, a coverage table and the full API reference.
The original streetlevel documentation is at [streetlevel.readthedocs.io](https://streetlevel.readthedocs.io/).

## Functionality overview
Services covering multiple countries are on the left; services covering one specific country are on the right.

✔ implemented / available; 🟡 partially implemented; ❌ not implemented; ⚫ not available / not applicable

<table>
  <thead>
    <th></th>
    <th align="center">Google<br>Street&nbsp;View</th>
    <th align="center">Apple<br>Look&nbsp;Around</th>
    <th align="center">Yandex<br>Panorama</th>
    <th align="center">Bing<br>Streetside</th>
    <th></th>
    <th align="center">🇨🇳 Baidu<br>Panorama</th>
    <th align="center">🇰🇷 Kakao<br>Road&nbsp;View</th>
    <th align="center">🇰🇷 Naver<br>Street&nbsp;View</th>
    <th align="center">🇨🇿 Mapy.cz<br>Panorama</th>
    <th align="center">🇮🇸 Já<br>360</th>
  </thead>
  <thead>
    <td colspan="11" style="padding-top:20px"><br><b>Finding panoramas</b><br>
      How panoramas can be retrieved through the API.
    </td>
  </thead>
  <tr>
    <td align="right">Find panoramas around a point</td>
    <td align="center">✔<sup>1</sup></td>
    <td align="center">⚫</td>
    <td align="center">✔<sup>1</sup></td>
    <td align="center">✔</td>
    <td></td>
    <td align="center">✔<sup>1</sup></td>
    <td align="center">✔</td>
    <td align="center">✔<sup>1</sup></td>
    <td align="center">✔<sup>1</sup></td>
    <td align="center">✔<sup>1</sup></td>
  </tr>
  <tr>
    <td align="right">Find panoramas by map tile or bbox</td>
    <td align="center">✔<sup>2</sup></td>
    <td align="center">✔<sup>2</sup></td>
    <td align="center">⚫</td>
    <td align="center">✔<sup>3</sup></td>
    <td></td>
    <td align="center">⚫</td>
    <td align="center">⚫</td>
    <td align="center">⚫</td>
    <td align="center">⚫</td>
    <td align="center">⚫</td>
  </tr>
  <tr>
    <td align="right">Get specific panorama by ID</td>
    <td align="center">✔</td>
    <td align="center">⚫</td>
    <td align="center">✔</td>
    <td align="center">✔</td>
    <td></td>
    <td align="center">✔</td>
    <td align="center">✔</td>
    <td align="center">✔</td>
    <td align="center">✔</td>
    <td align="center">✔</td>
  </tr>
  <thead>
    <td colspan="11" style="padding-top:20px"><br><b>Imagery</b><br>
      The type of imagery returned by the service.
    </td>
  </thead>
  <tr>
    <td align="right">Panoramas</td>
    <td align="center">✔</td>
    <td align="center">✔<sup>4</sup></td>
    <td align="center">✔</td>
    <td align="center">✔</td>
    <td></td>
    <td align="center">✔</td>
    <td align="center">✔</td>
    <td align="center">✔</td>
    <td align="center">✔</td>
    <td align="center">✔</td>
  </tr>
  <tr>
    <td align="right">Depth</td>
    <td align="center">✔<sup>5</sup></td>
    <td align="center">❌</td>
    <td align="center">⚫</td>
    <td align="center">⚫</td>
    <td></td>
    <td align="center">❌?<sup>10</sup></td>
    <td align="center">✔</td>
    <td align="center">✔<sup>14</sup></td>
    <td align="center">⚫<br></td>
    <td align="center">⚫<br></td>
  </tr>
  <tr>
    <td align="right">Image projection</td>
    <td align="center">Equirectangular</td>
    <td align="center">???</td>
    <td align="center">Equirectangular</td>
    <td align="center">Cubemap</td>
    <td></td>
    <td align="center">Equirectangular</td>
    <td align="center">Equirectangular</td>
    <td align="center">Equirectangular/Cubemap<sup>13</sup></td>
    <td align="center">Equirectangular</td>
    <td align="center">Cubemap</td>
  </tr>
  <tr>
    <td align="right">Image format</td>
    <td align="center">JPEG</td>
    <td align="center">HEIC</td>
    <td align="center">JPEG</td>
    <td align="center">JPEG</td>
    <td></td>
    <td align="center">JPEG</td>
    <td align="center">JPEG</td>
    <td align="center">JPEG</td>
    <td align="center">JPEG</td>
    <td align="center">JPEG</td>
  </tr>
  <thead>
    <td colspan="11" style="padding-top:20px"><br><b>Available metadata</b><br>
      Metadata returned by the API of the service alongside ID and location.
    </td>
  </thead>
  <tr>
    <td align="right">Capture date</td>
    <td align="center">✔<sup>6</sup></td>
    <td align="center">✔</td>
    <td align="center">✔</td>
    <td align="center">✔</td>
    <td></td>
    <td align="center">✔</td>
    <td align="center">✔</td>
    <td align="center">✔</td>
    <td align="center">✔</td>
    <td align="center">✔<sup>9</sup></td>
  </tr>
  <tr>
    <td align="right">Heading, pitch, roll</td>
    <td align="center">✔</td>
    <td align="center">✔</td>
    <td align="center">✔<sup>7</sup></td>
    <td align="center">✔</td>
    <td></td>
    <td align="center">✔</td>
    <td align="center">✔<sup>7</sup></td>
    <td align="center">✔<sup>11</sup></td>
    <td align="center">✔</td>
    <td align="center">✔<sup>7</sup></td>
  </tr>
  <tr>
    <td align="right">Elevation</td>
    <td align="center">✔</td>
    <td align="center">✔</td>
    <td align="center">⚫</td>
    <td align="center">✔</td>
    <td></td>
    <td align="center">✔</td>
    <td align="center">⚫</td>
    <td align="center">⚫<sup>12</sup></td>
    <td align="center">✔</td>
    <td align="center">⚫</td>
  </tr>
  <tr>
    <td align="right">Nearby / linked panoramas</td>
    <td align="center">✔</td>
    <td align="center">⚫</td>
    <td align="center">✔</td>
    <td align="center">✔<sup>8</sup></td>
    <td></td>
    <td align="center">✔</td>
    <td align="center">✔</td>
    <td align="center">✔</td>
    <td align="center">✔</td>
    <td align="center">✔</td>
  </tr>
  <tr>
    <td align="right">Historical panoramas</td>
    <td align="center">✔</td>
    <td align="center">⚫</td>
    <td align="center">✔</td>
    <td align="center">⚫</td>
    <td></td>
    <td align="center">✔</td>
    <td align="center">✔</td>
    <td align="center">✔</td>
    <td align="center">✔</td>
    <td align="center">⚫</td>
  </tr>
  <tr>
    <td align="right">Address</td>
    <td align="center">✔</td>
    <td align="center">⚫</td>
    <td align="center">✔</td>
    <td align="center">⚫</td>
    <td></td>
    <td align="center">⚫</td>
    <td align="center">✔</td>
    <td align="center">✔</td>
    <td align="center">⚫</td>
    <td align="center">✔</td>
  </tr>
  <tr>
    <td align="right">PoIs</td>
    <td align="center">✔</td>
    <td align="center">❌</td>
    <td align="center">✔</td>
    <td align="center">⚫</td>
    <td></td>
    <td align="center">⚫</td>
    <td align="center">❌</td>
    <td align="center">❌</td>
    <td align="center">⚫</td>
    <td align="center">⚫</td>
  </tr>
  <tr>
    <td align="right">Creator</td>
    <td align="center">✔</td>
    <td align="center">⚫</td>
    <td align="center">✔</td>
    <td align="center">⚫</td>
    <td></td>
    <td align="center">✔</td>
    <td align="center">⚫</td>
    <td align="center">⚫</td>
    <td align="center">✔</td>
    <td align="center">⚫</td>
  </tr>
</table>

1: Returns closest only  
2: Tile, z=17  
3: Bounding box  
4: Unstitched  
5: Appears to be a synthetic depth map created from elevation data and building footprints  
6: Month and year only for official coverage, full date for inofficial coverage  
7: Only heading; pitch/roll do not appear to be available  
8: Previous and next image in sequence  
9: Month and year only  
10: There is a `has_depth` field in the raw metadata, but I've yet to find a panorama that actually has depth  
11: Pitch/roll are only available for the new 3D imagery  
12: Camera altitude is available, however  
13: 3D imagery panos have both an equirectangular and a cubemap version; everything else is only available as cubemap  
14: Non-3D imagery appears to use a synthetic depthmap created from elevation data and building footprints
