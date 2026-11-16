# Street assets

Mapillary does not only store images: it detects objects in them and triangulates many of them to a map position.
mirrorworld exposes all three layers.

```{figure} ../_static/teasers/naip_poles.jpg
:class: mw-figure
:alt: Map features plotted over aerial imagery

Utility poles (yellow), manholes (blue), street lights (orange) and junction boxes (pink) from
`find_map_features()`, plotted on NAIP aerial imagery with mirrorworld. Mapillary CC BY-SA 4.0; NAIP public domain.
```

## Map features: objects with a position

```python
from mirrorworld import mapillary

poles = mapillary.find_map_features(
    51.5074, -0.1278, radius=150,
    values=["object--support--utility-pole", "object--junction-box",
            "object--manhole", "regulatory--"],
)
for f in poles[:5]:
    print(f.value, round(f.distance), "m", f.first_seen.date(), "->", f.last_seen.date())

pole = mapillary.find_map_feature_by_id(poles[0].id)   # adds facing direction and image IDs
print(pole.image_ids)                                  # every image that shows it
```

`values` entries match exactly, or as a prefix when they end in `--` (`"regulatory--"` = all regulatory signs).
Point classes are listed at [mapillary.com/developer/api-documentation/points](https://www.mapillary.com/developer/api-documentation/points),
traffic signs (`layer="traffic_sign"`) at [.../traffic-signs](https://www.mapillary.com/developer/api-documentation/traffic-signs).

:::{admonition} Teaser: one downtown z14 tile
:class: tip
A single Mapillary coverage tile over downtown Seattle holds about **21,600 utility poles, 53,600 manholes and 5,700
junction boxes**. Around Charing Cross, London: 519 street lights, 207 manholes and 29 junction boxes within 150 m.
:::

## Detections: per-image segmentation

```python
from collections import Counter

detections = mapillary.get_detections(pole.image_ids[0])
print(Counter(d.value for d in detections).most_common(5))
# e.g. [('construction--flat--sidewalk', 31), ('construction--flat--road', 27), ('object--support--pole', 12), ...]
```

Polygons are lists of rings of `(x, y)` in 0..1 image coordinates (origin top left), ready to scale to any download
size. The street-level teaser on the [previous page](street-level.md) was drawn exactly this way.

## Point clouds: the scene in 3D

```python
cloud = mapillary.get_point_cloud(pole.image_ids[0])
cloud.xyz        # (N, 3) east/north/up metres around cloud.reference
cloud.rgb        # (N, 3) colours
cloud.to_wgs84() # (N, 3) lat, lon, height
cloud.reconstruction["shots"]   # camera poses of every image in the reconstruction (OpenSfM format)
```

**API:** {doc}`../reference/mirrorworld.mapillary`
