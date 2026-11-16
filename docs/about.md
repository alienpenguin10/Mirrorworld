# About

## Credits

mirrorworld is a fork of [**streetlevel**](https://github.com/sk-zk/streetlevel) by sk-zk, which provides the
street-level providers (Street View, Look Around, Streetside, Yandex, Baidu, Kakao, Naver, Mapy.cz, Já 360).
mirrorworld adds the open street-level platforms, street assets, aerial, satellite, elevation, LiDAR, map-service and
OpenStreetMap modules. See [CREDITS.md](https://github.com/alienpenguin10/Mirrorworld/blob/main/CREDITS.md) for
third-party code acknowledged by streetlevel.

The code is MIT licensed ([LICENSE](https://github.com/alienpenguin10/Mirrorworld/blob/main/LICENSE)).

## Data terms

mirrorworld hosts no data: every request goes to the original provider, and **each provider's terms apply to what you
download**. Most modules state their licence in `raster.metadata["license"]` and in their docstring.

- Open licences: Mapillary, KartaView and Panoramax (CC BY-SA 4.0), PDOK (CC BY 4.0), AHN (CC0), Environment Agency and
  Welsh Government LiDAR (OGL v3), USGS and NAIP (public domain), Copernicus Sentinel and DEM data (free and open,
  with attribution), ESA WorldCover (CC BY 4.0), OpenStreetMap (ODbL).
- Esri World Imagery and Wayback: Esri's terms of use.
- Bing, Google and the street-level providers inherited from streetlevel use internal or unofficial endpoints. They
  may change without notice; check the provider's terms before relying on them, and keep request volumes modest.

## Image credits

All images in these docs were fetched and rendered with mirrorworld
([script](https://github.com/alienpenguin10/Mirrorworld/blob/main/docs/scripts/make_teasers.py)).

| Image | Source |
|---|---|
| Dam square, aerial and OSM overlay | PDOK / Beeldmateriaal Nederland, CC BY 4.0; (c) OpenStreetMap contributors, ODbL |
| Vondelpark, colour-infrared | PDOK / Beeldmateriaal Nederland, CC BY 4.0 |
| Amsterdam object heights | AHN via PDOK, CC0 |
| Street-level segmentation | Mapillary (image and detections), CC BY-SA 4.0 |
| Utility poles on aerial imagery | Mapillary map features, CC BY-SA 4.0; USDA NAIP, public domain |
| NAIP false colour | USDA NAIP, public domain |
| Seattle NDVI | Contains modified Copernicus Sentinel data 2025 |
| Seattle LiDAR | USGS 3DEP (King County 2021), public domain |
| London object heights | Environment Agency LiDAR, Open Government Licence v3.0 |
| Wayback timeline | Capture dates from Esri World Imagery Wayback metadata |

## Changelog

**0.1.1** — `sentinel2`: Earth Search scenes whose BOA offset is already removed (`earthsearch:boa_offset_applied`)
now report `offset: 0` in `band_info`; 0.1.0 reported the catalogue's `-0.1`, which made dark surfaces negative and
NDVI wrong. New documentation site, a `Documentation` link and per-version Python classifiers on PyPI.

**0.1.0** (2026-11-15) — first release: street-level (incl. Mapillary, KartaView, Panoramax), street assets, aerial
tiles, Wayback, PDOK, STAC satellite presets, elevation (EA, Wales, AHN, 3DEP, Copernicus), LiDAR, generic map
services and OpenStreetMap.
