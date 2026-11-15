# Mirrorworld addition (not in upstream streetlevel).
"""
Dutch national aerial photography from PDOK (Beeldmateriaal Nederland): yearly nationwide orthophotos in RGB and
colour-infrared (near-infrared, red, green), at 8 cm (5 cm in parts of 2025-2026) and 25 cm, from 2016 on.
Open data (CC BY 4.0), no key. Served in the Dutch national grid (EPSG:28992) by default.
"""
from typing import List, Optional, Union

from aiohttp import ClientSession

from ...raster import Raster
from ...services import wms

RGB_URL = "https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0"
CIR_URL = "https://service.pdok.nl/hwh/luchtfotocir/wms/v1_0"
NATIVE_CRS = "EPSG:28992"
EXTENT = (53.64, 3.17, 50.58, 7.49)
"""(north, west, south, east) of the imagery as advertised by the service; outside it the service returns blank
images, so requests that miss it are refused."""


def _check_extent(north, west, south, east):
    n, w, s_, e = EXTENT
    if north <= s_ or south >= n or east <= w or west >= e:
        raise ValueError("PDOK imagery covers the Netherlands only; the bounding box is outside it")


def list_layers(infrared: bool = False) -> List[wms.WmsLayer]:
    """
    Lists the available years and resolutions.

    :param infrared: *(optional)* List the colour-infrared layers instead of RGB. Defaults to False.
    :return: WmsLayer objects; names look like ``2024_orthoHR`` (8 cm) or ``2024_ortho25IR`` (25 cm infrared).
    """
    return wms.get_layers(CIR_URL if infrared else RGB_URL)


def layer_name(year: Union[int, str, None] = None, infrared: bool = False, high_resolution: bool = True) -> str:
    """
    Builds a layer name.

    :param year: *(optional)* Year, or None for the most recent imagery everywhere ("Actueel").
    :param infrared: *(optional)* Colour-infrared instead of RGB. Defaults to False.
    :param high_resolution: *(optional)* 8 cm ("HR") instead of 25 cm. Defaults to True.
    :return: e.g. ``Actueel_orthoHR`` or ``2023_ortho25IR``.
    """
    prefix = "Actueel" if year is None else str(year)
    return f"{prefix}_ortho{'HR' if high_resolution else '25'}{'IR' if infrared else ''}"


def get_raster(north: float, west: float, south: float, east: float, year: Union[int, str, None] = None,
               infrared: bool = False, resolution: float = 0.08, crs: str = NATIVE_CRS,
               layer: Optional[str] = None, max_size: int = 2000, max_concurrency: int = 4) -> Raster:
    """
    Downloads Dutch orthophotos for a bounding box.

    :param north: Latitude of the top edge.
    :param west: Longitude of the left edge.
    :param south: Latitude of the bottom edge.
    :param east: Longitude of the right edge.
    :param year: *(optional)* Year, or None for the most recent imagery. Defaults to None.
    :param infrared: *(optional)* Colour-infrared (bands: near-infrared, red, green) instead of RGB.
        Defaults to False.
    :param resolution: *(optional)* Pixel size in meters. Values below 0.25 use the high-resolution layers,
        which do not exist for every year (see :func:`list_layers`). Defaults to 0.08.
    :param crs: *(optional)* Output CRS. Defaults to EPSG:28992.
    :param layer: *(optional)* Explicit layer name, overriding ``year``/``infrared``/``resolution`` choice.
    :param max_size: *(optional)* Largest image side per request. Defaults to 2000.
    :param max_concurrency: *(optional)* Maximum number of simultaneous requests. Defaults to 4.
    :return: The raster.
    """
    _check_extent(north, west, south, east)
    layer = layer or layer_name(year, infrared, resolution < 0.25)
    raster = wms.get_raster(CIR_URL if infrared or layer.endswith("IR") else RGB_URL, layer, north, west, south,
                            east, resolution=resolution, crs=crs, image_format="image/png", max_size=max_size,
                            max_concurrency=max_concurrency)
    raster.band_names = ["nir", "red", "green"] if layer.endswith("IR") else ["red", "green", "blue"]
    raster.metadata.update({"provider": "PDOK / Beeldmateriaal Nederland", "license": "CC BY 4.0"})
    return raster


async def get_raster_async(north: float, west: float, south: float, east: float, session: ClientSession,
                           year: Union[int, str, None] = None, infrared: bool = False, resolution: float = 0.08,
                           crs: str = NATIVE_CRS, layer: Optional[str] = None, max_size: int = 2000,
                           max_concurrency: int = 4) -> Raster:
    _check_extent(north, west, south, east)
    layer = layer or layer_name(year, infrared, resolution < 0.25)
    raster = await wms.get_raster_async(CIR_URL if infrared or layer.endswith("IR") else RGB_URL, layer, north,
                                        west, south, east, session, resolution=resolution, crs=crs,
                                        image_format="image/png", max_size=max_size, max_concurrency=max_concurrency)
    raster.band_names = ["nir", "red", "green"] if layer.endswith("IR") else ["red", "green", "blue"]
    raster.metadata.update({"provider": "PDOK / Beeldmateriaal Nederland", "license": "CC BY 4.0"})
    return raster


def download_raster(north: float, west: float, south: float, east: float, path: str, **kwargs) -> Raster:
    """
    Same as :func:`get_raster`, then saves the result (see :meth:`streetlevel.raster.Raster.save`).

    :param path: Output path.
    :return: The raster.
    """
    raster = get_raster(north, west, south, east, **kwargs)
    raster.save(path)
    return raster
