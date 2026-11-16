# LiDAR point clouds

```{figure} ../_static/teasers/lidar_city.jpg
:class: mw-figure
:alt: LiDAR point cloud of downtown Seattle

Downtown Seattle from the King County 2021 survey, fetched with `usgs3dep.get_points(resolution=1.5)` and plotted
with matplotlib. USGS 3DEP, public domain.
```

Point clouds are huge; mirrorworld reads **Entwine Point Tile** octrees and downloads only the nodes that intersect
your box, down to the point spacing you ask for.

```python
from mirrorworld.lidar import usgs3dep

print(usgs3dep.find_datasets(47.6075, -122.3360, 47.6045, -122.3310))   # surveys covering the box, newest first
las = usgs3dep.get_points(47.6075, -122.3360, 47.6045, -122.3310, resolution=1.0)
ground = las.points[las.classification == 2]
las.write("downtown.laz")
```

The result is a regular [`laspy.LasData`](https://laspy.readthedocs.io/) in EPSG:3857 with its CRS in the header.

| Parameter | Effect |
|---|---|
| `resolution` | target point spacing (m); skips deeper octree levels |
| `classes` | keep ASPRS classes, e.g. `[2]` ground, `[6]` building |
| `max_points` | refuse accidental city-sized requests (default 50 million) |

## Other EPT datasets

```python
from mirrorworld.lidar import ept

info = ept.get_info("https://.../my-dataset")          # any public EPT
las = ept.get_points(info.url, north, west, south, east, resolution=2.0)
```

Needs `pip install "mirrorworld[lidar]"`. **API:** {doc}`../reference/mirrorworld.lidar`
