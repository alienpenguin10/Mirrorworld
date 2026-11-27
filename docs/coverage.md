# Coverage

Where each source works, checked against the live services. ✅ available · 🟡 patchy · ❌ not available ·
"UK" columns were tested at Charing Cross (London), Cornhill (Ipswich) and central Guildford in November 2026.

```{list-table}
:header-rows: 1
:class: mw-coverage

* - Source
  - Module
  - Worldwide
  - UK
  - Netherlands
  - United States
  - Key
* - Mapillary images and assets
  - `mapillary`
  - 🟡 crowd-sourced
  - ✅ dense in cities
  - ✅
  - ✅
  - free token
* - KartaView
  - `kartaview`
  - 🟡
  - 🟡 sparse, 2018-21
  - 🟡
  - 🟡
  - none
* - Panoramax
  - `panoramax`
  - 🟡 strongest in France
  - ❌ none at test sites
  - 🟡
  - 🟡
  - none
* - Google / Look Around / Streetside / ...
  - `streetview`, ...
  - per provider
  - ✅ Street View
  - ✅
  - ✅
  - none
* - Bing, Google, Esri tiles
  - `aerial.*`
  - ✅
  - ✅ ~9 cm (Bing)
  - ✅
  - ✅
  - none
* - Esri Wayback
  - `aerial.wayback`
  - ✅
  - ✅ 4-6 captures since 2013
  - ✅
  - ✅
  - none
* - PDOK orthophotos
  - `aerial.pdok`
  - ❌
  - ❌
  - ✅ 8 cm RGB + CIR
  - ❌
  - none
* - USGS tiles / NAIP
  - `aerial.usgs`, `satellite.naip`
  - ❌
  - ❌
  - ❌
  - ✅
  - none
* - Sentinel-2, Sentinel-1, Landsat, WorldCover
  - `satellite.*`
  - ✅
  - ✅
  - ✅
  - ✅
  - none
* - Environment Agency LiDAR
  - `elevation.ea`, `lidar.ea`
  - ❌
  - ✅ England, 1 m; NLP point clouds
  - ❌
  - ❌
  - none
* - Welsh LiDAR
  - `elevation.wales`
  - ❌
  - ✅ Wales, 1 m
  - ❌
  - ❌
  - none
* - AHN
  - `elevation.ahn`
  - ❌
  - ❌
  - ✅ 0.5 m
  - ❌
  - none
* - USGS 3DEP DEM and point clouds
  - `elevation.usgs3dep`, `lidar.usgs3dep`
  - ❌
  - ❌
  - ❌
  - ✅
  - none
* - Copernicus DEM
  - `elevation.copernicus`
  - ✅ 30 m
  - ✅
  - ✅
  - ✅
  - none
* - OpenStreetMap
  - `vector.osm`
  - ✅
  - 🟡 assets sparsely tagged
  - ✅
  - ✅
  - none
```

Outside a dataset's area, mirrorworld raises a `ValueError` that says where the data exists, instead of returning a
blank or all-zero raster. Scotland's public LiDAR is only offered as rendered map images and 10 km tile downloads, so
it is not wrapped yet; any service with a WMS/WCS or COG can be read with the [generic clients](guides/map-services.md).
