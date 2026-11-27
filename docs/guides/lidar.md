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

## England: Environment Agency National LIDAR Programme

The Environment Agency publishes its survey point clouds only as whole 5 km British National Grid tiles (one zipped
LAZ per tile and survey year, 0.2-0.4 GB). `lidar.ea` asks the service which tiles and years cover your box,
downloads each tile once into a cache directory and crops it locally, reading in chunks so a tile never sits in
memory.

```python
from mirrorworld.lidar import ea

for t in ea.search(51.5085, -0.1290, 51.5070, -0.1260):          # Trafalgar Square
    print(t.tile, t.year)                                         # TQ2580 2020, TQ2580 2018, TQ3080 2020, ...
print(ea.find_years("TL4055"))                                    # [2023, 2019]
las = ea.get_points(51.5085, -0.1290, 51.5070, -0.1260, classes=[2, 6], directory="data/ea-lidar")
```

- Points are in **EPSG:27700** (British National Grid), heights in meters above Ordnance Datum Newlyn,
  classes 1 unclassified, 2 ground, 3-5 vegetation, 6 building, 7 noise; no RGB. Surveys up to 2021 are mostly
  LAS 1.2 point format 1, later ones LAS 1.4 point format 6 (mixed tiles are converted to one format). About
  2-6 points/m², higher in recent years.
- Tiles keep the provider's file name, which records the survey project and flight dates
  (`TL4055_P_12744_20230213_20230213.laz`); a "2018" survey can have been flown in December 2017.
- `year=None` takes each tile's newest survey, so a box across a tile edge can mix years; pass `year=` to fix one.
- `max_tiles` (default 4) stops accidental multi-gigabyte downloads. The cache defaults to
  `~/.cache/mirrorworld/ea-lidar`, or `$MIRRORWORLD_CACHE/ea-lidar`.
- `ea.search(..., product=None)` lists every survey product for the box: the NLP DTM/DSM/intensity rasters, the
  2022 composites and the older `lidar_point_cloud` surveys (2006-2012 and some since).
- Use `search`, not guessed URLs, to find years: the service rate-limits bursts (mirrorworld backs off and retries)
  and, when busy, answers "no data" for tiles that exist.
- The box is converted from WGS84 to EPSG:27700 by PROJ; without the OSTN15 grid (PROJ network or
  `projsync`) that conversion is only good to a few meters, which matters for the crop edge, not for the points.

Open Government Licence v3; attribute the Environment Agency.

## Other EPT datasets

```python
from mirrorworld.lidar import ept

info = ept.get_info("https://.../my-dataset")          # any public EPT
las = ept.get_points(info.url, north, west, south, east, resolution=2.0)
```

Needs `pip install "mirrorworld[lidar]"`. **API:** {doc}`../reference/mirrorworld.lidar`
