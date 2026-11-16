# Aerial imagery

```{figure} ../_static/teasers/amsterdam_rgb.jpg
:class: mw-figure
:alt: 8 cm aerial photo of Dam square

Dam square, Amsterdam, at 8 cm from `aerial.pdok`. PDOK / Beeldmateriaal Nederland, CC BY 4.0.
```

## Web tiles at up to ~10 cm

`bing`, `google`, `esri` and `usgs` share one interface. Ask for a resolution, or let mirrorworld find the finest
zoom available at the centre of your box:

```python
from mirrorworld.aerial import bing, esri

print(bing.find_max_zoom(51.5074, -0.1278))          # 20 -> ~0.09 m per pixel in London
img = esri.download_image(51.5079, -0.1287, 51.5070, -0.1269, "charing_cross.jpg")
print(img.ground_resolution, img.metadata)
```

Results are stitched in Web Mercator and saved with a world file, a GDAL `.aux.xml` and a `.json` with zoom,
resolution and capture dates. From the shell:

```bash
python -m mirrorworld.aerial esri 51.5079 -0.1287 51.5070 -0.1269 out.jpg --resolution 0.2
python -m mirrorworld.aerial bing 51.5079 -0.1287 51.5070 -0.1269 --max-zoom
```

| Provider | Typical max zoom (London) | Notes |
|---|---|---|
| Bing | 20 (≈0.09 m) | capture dates in metadata |
| Google | 22 (upsampled beyond native) | |
| Esri World Imagery | 19 (≈0.19 m) | see Wayback for history |
| USGS | 16 (US only) | |

:::{warning}
Bing and Google tiles use unofficial endpoints; check their terms before relying on them, and keep request volumes
modest.
:::

## Time travel with Wayback

Esri has archived every release of World Imagery since 2014. `find_versions` lists only the releases that actually
changed your location, with capture dates:

```{figure} ../_static/teasers/wayback_timeline.png
:alt: Timeline of distinct captures
```

```python
from mirrorworld.aerial import wayback

versions = wayback.find_versions(51.5074, -0.1278)
for v in versions:
    print(v.capture_date, v.resolution, v.provider)
wayback.download_image(51.5079, -0.1287, 51.5070, -0.1269, "then.jpg", release=versions[-1])
wayback.download_image(51.5079, -0.1287, 51.5070, -0.1269, "now.jpg", release=versions[0])
```

## National orthophotos: the Netherlands

```{figure} ../_static/teasers/amsterdam_cir.jpg
:class: mw-figure
:alt: Colour-infrared aerial photo

Vondelpark, Amsterdam, in colour-infrared: vegetation glows red. PDOK, CC BY 4.0.
```

```python
from mirrorworld.aerial import pdok

pdok.download_raster(52.3606, 4.8740, 52.3588, 4.8790, "vondelpark_cir.png", year=2025, infrared=True)
[l.name for l in pdok.list_layers()]       # yearly layers 2016-2026, 8 cm and 25 cm
```

Other countries publish orthophotos through standard services: point the [generic clients](map-services.md) at them.

**API:** {doc}`../reference/mirrorworld.aerial`
