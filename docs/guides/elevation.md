# Elevation

Terrain (DTM, bare ground), surface (DSM, tops of things) and **object heights** (nDSM = DSM − DTM) for a box.

::::{grid} 1 1 2 2
:gutter: 2

:::{grid-item}
```{figure} ../_static/teasers/amsterdam_ndsm.jpg
:class: mw-figure
:alt: Object heights in Amsterdam

`ahn.get_ndsm()` at 0.5 m, Dam square. AHN, CC0.
```
:::

:::{grid-item}
```{figure} ../_static/teasers/london_ndsm.jpg
:class: mw-figure
:alt: Object heights in London

`ea.get_ndsm()` at 1 m, Trafalgar Square. Environment Agency, OGL v3.
```
:::

::::

| Module | Products | Resolution | Coverage | Licence |
|---|---|---|---|---|
| `ea` | DTM, first-return DSM, nDSM | 1 m | England | OGL v3 |
| `wales` | DSM, DTM, nDSM | 1 m | Wales | OGL v3 |
| `ahn` | DSM, DTM, nDSM | 0.5 m | Netherlands | CC0 |
| `usgs3dep` | bare-earth DEM | down to 1 m | United States | public domain |
| `copernicus` | surface model (GLO-30) | 30 m | worldwide | Copernicus DEM licence |

```python
from mirrorworld.elevation import ea, copernicus

heights = ea.get_ndsm(51.5090, -0.1300, 51.5072, -0.1262)    # metres above ground, EPSG:27700
print(heights.data.max())                                    # Nelson's Column and the National Gallery
heights.save("trafalgar_ndsm.tif")

dem = copernicus.get_raster(47.615, -122.345, 47.600, -122.325)  # anywhere on Earth
```

:::{note}
The Environment Agency service occasionally stalls single requests; mirrorworld retries them, so a box can take tens
of seconds. Outside each dataset's area you get a clear `ValueError`.
:::

**API:** {doc}`../reference/mirrorworld.elevation`
