# Street-level imagery

Twelve services behind the same handful of verbs: **find** panoramas near a point, **fetch** one by ID, **get** or
**download** the image.

```{figure} ../_static/teasers/mapillary_detections.jpg
:class: mw-figure
:alt: Street-level image with segmentation overlay

A Mapillary image with Mapillary's own segmentation drawn on top — see [street assets](street-assets.md).
Image CC BY-SA 4.0 via Mapillary.
```

## The pattern

::::{tab-set}

:::{tab-item} Mapillary
```python
from mirrorworld import mapillary

pics = mapillary.find_panoramas(51.5074, -0.1278, radius=50, panos_only=True)
pano = mapillary.find_panorama_by_id(pics[0].id)     # adds camera, corrected pose and image URLs
mapillary.download_panorama(pano, f"{pano.id}.jpg", size="original")
images_in_sequence = mapillary.get_sequence(pano.sequence_id)
```
:::

:::{tab-item} Panoramax
```python
from mirrorworld import panoramax

pics = panoramax.find_panoramas(51.5088, -0.1270, radius=30)
panoramax.download_panorama(pics[0], f"{pics[0].id}.jpg", size="hd")
```
:::

:::{tab-item} KartaView
```python
from mirrorworld import kartaview

photos = kartaview.find_panoramas(47.6062, -122.3321, radius=100)
for photo in photos:                      # closest first
    try:
        kartaview.download_panorama(photo, f"{photo.id}.jpg")
        break
    except RuntimeError:                  # some old photos have been removed from KartaView's storage
        continue
```
:::

:::{tab-item} Google Street View
```python
from mirrorworld import streetview

pano = streetview.find_panorama(46.883958, 12.169002)
streetview.download_panorama(pano, f"{pano.id}.jpg")
```
:::

::::

## Services

| Service | Module | Coverage | Licence / access |
|---|---|---|---|
| Mapillary | `mapillary` | worldwide, crowd-sourced; dense in many cities | CC BY-SA 4.0, free token |
| KartaView | `kartaview` | worldwide, patchy | CC BY-SA 4.0, no key |
| Panoramax | `panoramax` | federated; strongest in France | mostly CC BY-SA 4.0, no key |
| Google Street View | `streetview` | worldwide | internal API |
| Apple Look Around | `lookaround` | selected countries | internal API |
| Bing Streetside | `streetside` | US, parts of Europe | internal API |
| Yandex, Baidu, Kakao, Naver, Mapy.cz, Já 360 | `yandex`, `baidu`, `kakao`, `naver`, `mapy`, `ja` | their home countries | internal APIs |

The open platforms (Mapillary, KartaView, Panoramax) mix 360° panoramas with ordinary photos; check
`pano.is_equirectangular` (or `is_pano` on Mapillary). Headings are radians, 0 = north, clockwise.

:::{admonition} Provider quirks we handle for you
:class: note

- **Mapillary**'s bounding-box search fails in dense cities, so `find_panoramas` reads Mapillary's vector coverage
  tiles instead and returns results closest first.
- **Panoramax**'s own point search returns pictures *looking at* a place; `find_panoramas` returns pictures *taken
  near* it.
- **KartaView** storage hosts are flaky; downloads fall back to its CDN copy automatically.
:::

## Async

```python
import asyncio
from aiohttp import ClientSession
from mirrorworld import mapillary

async def main():
    async with ClientSession() as session:
        pics = await mapillary.find_panoramas_async(51.5074, -0.1278, session, radius=50)
        await mapillary.download_panorama_async(pics[0], "p.jpg", session, size="2048")

asyncio.run(main())
```

**API:** {doc}`../reference/mirrorworld.mapillary` · {doc}`../reference/mirrorworld.panoramax` ·
{doc}`../reference/mirrorworld.kartaview` · {doc}`../reference/mirrorworld.streetview` and the other providers in the
[reference](../reference/index.md).
