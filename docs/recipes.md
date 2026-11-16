# Recipes

Short, complete programs that combine modalities. Each one runs as is (Mapillary recipes need
`MAPILLARY_ACCESS_TOKEN`; raster recipes need `mirrorworld[raster]`).

## Everything about one block

Pull a matching stack of layers for a single box and save them side by side, ready for QGIS or a model.

```python
from pathlib import Path
from mirrorworld import mapillary
from mirrorworld.elevation import ea
from mirrorworld.satellite import sentinel2
from mirrorworld.aerial import esri
from mirrorworld.vector import osm
import json

box = (51.5090, -0.1300, 51.5072, -0.1262)            # Trafalgar Square, London
lat, lon = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
out = Path("trafalgar"); out.mkdir(exist_ok=True)

esri.download_image(*box, out / "aerial.jpg")
ea.download_ndsm(*box, out / "heights.tif")
sentinel2.download_raster(*box, out / "s2.tif", bands=("blue", "green", "red", "nir"))
(out / "footways.geojson").write_text(json.dumps(osm.find_features(*box, {"highway": ["footway", "pedestrian"]})))
for pano in mapillary.find_panoramas(lat, lon, radius=40, panos_only=True)[:3]:
    mapillary.download_panorama(pano, out / f"pano_{pano.id}.jpg", size="2048")
```

## Every image of every utility pole

Find triangulated poles, then download each image Mapillary saw them in — a ready-made weakly labelled dataset.

```python
from mirrorworld import mapillary

poles = mapillary.find_map_features(47.6800, -122.3000, radius=200, values=["object--support--utility-pole"])
for pole in poles[:10]:
    detail = mapillary.find_map_feature_by_id(pole.id)
    for image_id in (detail.image_ids or [])[:3]:
        mapillary.download_panorama(image_id, f"pole_{pole.id}_{image_id}.jpg", size="1024")
```

## Then and now

Download the oldest and newest distinct Esri captures of a place.

```python
from mirrorworld.aerial import wayback

box = (51.5079, -0.1287, 51.5070, -0.1269)
versions = wayback.find_versions((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)
for label, version in (("then", versions[-1]), ("now", versions[0])):
    wayback.download_image(*box, f"{label}_{version.capture_date}.jpg", release=version)
```

## Vegetation index in a few lines

```python
import numpy as np
from mirrorworld.satellite import sentinel2

r = sentinel2.get_raster(51.53, -0.18, 51.50, -0.12, bands=("red", "nir"), start="2025-05-01", end="2025-08-31")
s = r.metadata["band_info"]["red"]
red, nir = (r.band(b) * s["scale"] + s["offset"] for b in ("red", "nir"))                 # reflectance
valid = (r.band("red") != r.nodata) & (nir + red > 0.01)     # skip no-data and near-black pixels
ndvi = (nir - red) / np.where(valid, nir + red, 1)
print("mean NDVI", round(float(ndvi[valid].mean()), 3))
```

## Tallest objects in a box

```python
import numpy as np
from mirrorworld.elevation import ea

heights = ea.get_ndsm(51.5090, -0.1300, 51.5072, -0.1262)
row, col = np.unravel_index(np.argmax(heights.data[0]), heights.data[0].shape)
a, _, x0, _, e, y0 = heights.transform
print(f"{heights.data[0].max():.1f} m at E{x0 + a * (col + .5):.0f} N{y0 + e * (row + .5):.0f} (EPSG:27700)")
```

## Ground points from LiDAR as a CSV

```python
import numpy as np
from mirrorworld.lidar import usgs3dep

las = usgs3dep.get_points(47.6075, -122.3360, 47.6045, -122.3310, resolution=2.0, classes=[2])
np.savetxt("ground.csv", np.column_stack([las.x, las.y, las.z]), delimiter=",", header="x,y,z", comments="")
```

## Many places at once (async)

```python
import asyncio
from aiohttp import ClientSession
from mirrorworld import mapillary

places = {"London": (51.5074, -0.1278), "Ipswich": (52.0567, 1.1545), "Guildford": (51.2362, -0.5704)}

async def count(session, name, lat, lon):
    pics = await mapillary.find_panoramas_async(lat, lon, session, radius=50)
    return name, len(pics)

async def main():
    async with ClientSession() as session:
        for name, n in await asyncio.gather(*(count(session, k, *v) for k, v in places.items())):
            print(f"{name}: {n} images within 50 m")

asyncio.run(main())
```
