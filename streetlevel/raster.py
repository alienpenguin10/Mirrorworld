# Mirrorworld addition (not in upstream streetlevel).
"""
A georeferenced raster in any coordinate reference system, shared by the map-service, elevation and satellite
modules. Writing GeoTIFF and reading GeoTIFF responses need the optional ``rasterio`` dependency
(``pip install streetlevel[raster]``); PNG/JPEG output with a world file works without it.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
from PIL import Image


@dataclass
class Raster:
    """
    A georeferenced raster.

    ``transform`` uses the affine convention of rasterio/GDAL: a pixel's top left corner at column ``c`` and
    row ``r`` is at ``x = a*c + b*r + xoff`` and ``y = d*c + e*r + yoff``, stored as
    ``(a, b, xoff, d, e, yoff)``. For north-up rasters ``b = d = 0`` and ``e`` is negative.
    """

    data: np.ndarray
    """Pixel values with shape (bands, rows, columns)."""
    crs: str
    """Coordinate reference system, e.g. ``EPSG:28992``."""
    transform: Tuple[float, float, float, float, float, float]
    """Affine transform from pixel to CRS coordinates."""
    nodata: Optional[float] = None
    """Value marking pixels without data, if any."""
    band_names: Optional[List[str]] = None
    """Name of each band, e.g. ``["red", "green", "blue", "nir"]``."""
    metadata: dict = field(default_factory=dict)
    """Source information, e.g. service URL, layer, scene ID and acquisition date."""

    @property
    def width(self) -> int:
        return self.data.shape[2]

    @property
    def height(self) -> int:
        return self.data.shape[1]

    @property
    def count(self) -> int:
        """Number of bands."""
        return self.data.shape[0]

    @property
    def resolution(self) -> Tuple[float, float]:
        """Pixel width and height in CRS units."""
        return abs(self.transform[0]), abs(self.transform[4])

    @property
    def bounds(self) -> Tuple[float, float, float, float]:
        """Left, bottom, right, top in CRS units."""
        a, _, xoff, _, e, yoff = self.transform
        x0, x1 = xoff, xoff + a * self.width
        y0, y1 = yoff, yoff + e * self.height
        return min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)

    def band(self, name: str) -> np.ndarray:
        """Returns one band by name."""
        if not self.band_names or name not in self.band_names:
            raise KeyError(f"No band {name!r}; bands are {self.band_names}")
        return self.data[self.band_names.index(name)]

    def to_image(self, bands: Optional[List[str]] = None, percentiles: Tuple[float, float] = (2, 98)) -> Image.Image:
        """
        Renders one or three bands as an 8-bit PIL image, e.g. for previews or RGB inputs to a model.

        8-bit data is used as is; other data is stretched between the given percentiles.

        :param bands: *(optional)* Names of one or three bands. Defaults to the first three bands, or the first.
        :param percentiles: *(optional)* Low and high percentile of the contrast stretch. Defaults to (2, 98).
        :return: An ``L`` or ``RGB`` image.
        """
        if bands:
            array = np.stack([self.band(b) for b in bands])
        else:
            array = self.data[:3] if self.count >= 3 else self.data[:1]
        if array.dtype != np.uint8:
            values = array.astype(np.float64)
            valid = np.isfinite(values)
            if self.nodata is not None:
                valid &= values != self.nodata
            if valid.any():
                low, high = np.percentile(values[valid], percentiles)
            else:
                low, high = 0.0, 1.0
            scaled = np.clip((values - low) / max(high - low, 1e-12), 0, 1) * 255
            array = np.where(valid, scaled, 0).astype(np.uint8)
        if array.shape[0] == 1:
            return Image.fromarray(array[0], "L")
        return Image.fromarray(np.moveaxis(array, 0, -1), "RGB")

    def save(self, path: str, pil_args: dict = None) -> None:
        """
        Saves the raster with its georeferencing.

        ``.tif``/``.tiff`` writes a GeoTIFF with all bands, data type, CRS and nodata (needs ``rasterio``).
        ``.png``/``.jpg`` writes an 8-bit rendering (see :meth:`to_image`) with a world file and a GDAL
        ``.aux.xml`` CRS sidecar. Either way a ``.json`` file with ``metadata`` and band names is written
        beside it.

        :param path: Output path.
        :param pil_args: *(optional)* Additional arguments for PIL's ``Image.save`` (PNG/JPEG only).
        """
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        suffix = out.suffix.lower()
        if suffix in (".tif", ".tiff"):
            rasterio = require_rasterio()
            from rasterio.transform import Affine
            with rasterio.open(out, "w", driver="GTiff", width=self.width, height=self.height, count=self.count,
                               dtype=self.data.dtype, crs=self.crs, transform=Affine(*self.transform),
                               nodata=self.nodata, compress="deflate", tiled=True) as dst:
                dst.write(self.data)
                if self.band_names:
                    for i, name in enumerate(self.band_names, start=1):
                        dst.set_band_description(i, name)
        else:
            image = self.to_image()
            if pil_args is None:
                pil_args = {"quality": 95} if suffix in (".jpg", ".jpeg") else {}
            image.save(out, **pil_args)
            a, b, xoff, d, e, yoff = self.transform
            world = {".jpg": ".jgw", ".jpeg": ".jgw", ".png": ".pgw"}.get(suffix, ".wld")
            # World files reference the center of the top left pixel.
            out.with_suffix(world).write_text(
                f"{a}\n{d}\n{b}\n{e}\n{xoff + (a + b) / 2}\n{yoff + (d + e) / 2}\n")
            Path(str(out) + ".aux.xml").write_text(f"<PAMDataset><SRS>{self.crs}</SRS></PAMDataset>\n")
        sidecar = {"crs": self.crs, "transform": list(self.transform), "size_px": [self.width, self.height],
                   "bands": self.band_names, "nodata": self.nodata, "dtype": str(self.data.dtype),
                   "metadata": self.metadata}
        out.with_suffix(".json").write_text(json.dumps(sidecar, indent=2, default=str))


def require_rasterio():
    """Imports rasterio or explains how to install it."""
    try:
        import rasterio
        return rasterio
    except ImportError as e:
        raise ImportError("This function needs rasterio: pip install streetlevel[raster]") from e


def read_geotiff(data: bytes) -> Raster:
    """
    Decodes a GeoTIFF (e.g. a WCS or ArcGIS ``exportImage`` response).

    :param data: The file contents.
    :return: The raster.
    """
    rasterio = require_rasterio()
    from rasterio.io import MemoryFile
    with MemoryFile(data) as memfile, memfile.open() as src:
        return Raster(data=src.read(), crs=src.crs.to_string() if src.crs else None,
                      transform=tuple(src.transform)[:6], nodata=src.nodata,
                      band_names=[d for d in src.descriptions] if any(src.descriptions) else None)


def read_image(data: bytes) -> np.ndarray:
    """Decodes a PNG/JPEG into a (bands, rows, columns) uint8 array, dropping alpha."""
    image = Image.open(BytesIO(data))
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")
    array = np.asarray(image)
    return array[np.newaxis] if array.ndim == 2 else np.moveaxis(array, -1, 0)


def utm_crs(lat: float, lon: float) -> str:
    """
    Returns the WGS 84 / UTM zone CRS containing a point, a good default metric CRS for local work.

    :param lat: Latitude.
    :param lon: Longitude.
    :return: e.g. ``EPSG:32610`` for Seattle.
    """
    zone = int((lon + 180) // 6) % 60 + 1
    return f"EPSG:{32600 + zone if lat >= 0 else 32700 + zone}"


def bbox_to_crs(north: float, west: float, south: float, east: float, crs: str) -> Tuple[float, float, float, float]:
    """
    Transforms a WGS84 bounding box to another CRS, densifying the edges so the result encloses it.

    :return: minx, miny, maxx, maxy in the target CRS (in its x/y order, i.e. easting/northing for
        projected systems and longitude/latitude for geographic ones).
    """
    from pyproj import Transformer
    transformer = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    return transformer.transform_bounds(west, south, east, north, densify_pts=21)


def grid_for_bounds(bounds: Tuple[float, float, float, float], resolution: float,
                    snap: bool = True) -> Tuple[Tuple[float, float, float, float, float, float], int, int]:
    """
    Builds a north-up pixel grid covering ``bounds`` at ``resolution``.

    :param bounds: minx, miny, maxx, maxy.
    :param resolution: Pixel size in CRS units.
    :param snap: *(optional)* Align the grid to multiples of the resolution, so adjacent requests line up.
    :return: (transform, width, height).
    """
    minx, miny, maxx, maxy = bounds
    if snap:
        minx = math.floor(minx / resolution) * resolution
        maxy = math.ceil(maxy / resolution) * resolution
    width = max(1, math.ceil((maxx - minx) / resolution - 1e-9))
    height = max(1, math.ceil((maxy - miny) / resolution - 1e-9))
    return (resolution, 0.0, minx, 0.0, -resolution, maxy), width, height


def read_cog(url: str, north: float, west: float, south: float, east: float, resolution: Optional[float] = None,
             crs: Optional[str] = None, resampling: str = "nearest", band_names: Optional[List[str]] = None) -> Raster:
    """
    Reads a bounding box from any cloud-optimized GeoTIFF over HTTP, fetching only the bytes needed, e.g. the
    whole-country LiDAR models that national agencies publish as single COGs.

    :param url: HTTP(S) URL of the GeoTIFF.
    :param north: Latitude of the top edge.
    :param west: Longitude of the left edge.
    :param south: Latitude of the bottom edge.
    :param east: Longitude of the right edge.
    :param resolution: *(optional)* Pixel size in units of ``crs``. Defaults to the file's own.
    :param crs: *(optional)* Output CRS. Defaults to the file's own.
    :param resampling: *(optional)* Resampling method when the grid differs. Defaults to nearest.
    :param band_names: *(optional)* Names for the bands.
    :return: The raster.
    """
    from .satellite import stac
    from .satellite.scene import Scene
    scene = Scene(id=url.rsplit("/", 1)[-1], collection="cog", datetime=None, bbox=(west, south, east, north),
                  endpoint=url, assets={"data": {"href": url}})
    raster = stac.read(scene, ["data"], north, west, south, east, resolution=resolution, crs=crs,
                       resampling=resampling)
    raster.band_names = band_names or (["data"] if raster.count == 1 else [f"band_{i + 1}" for i in range(raster.count)])
    raster.metadata = {"source": "COG", "url": url}
    return raster
