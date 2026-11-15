# Mirrorworld addition (not in upstream streetlevel). Offline: no network requests.
import asyncio

import numpy as np
from pytest import approx

from streetlevel.services import wms, wmts, wcs
from streetlevel.services.util import mosaic_async, is_north_first, meters_per_unit

WMS_CAPS = b"""<?xml version="1.0"?>
<WMS_Capabilities version="1.3.0" xmlns="http://www.opengis.net/wms"><Capability><Layer><Title>root</Title>
<Layer><Name>ortho</Name><Title>Ortho 8cm</Title><CRS>EPSG:28992</CRS><CRS>EPSG:3857</CRS>
<EX_GeographicBoundingBox><westBoundLongitude>3.1</westBoundLongitude><eastBoundLongitude>7.5</eastBoundLongitude>
<southBoundLatitude>50.5</southBoundLatitude><northBoundLatitude>53.6</northBoundLatitude></EX_GeographicBoundingBox>
</Layer></Layer></Capability></WMS_Capabilities>"""

WMTS_CAPS = b"""<?xml version="1.0"?>
<Capabilities xmlns="http://www.opengis.net/wmts/1.0" xmlns:ows="http://www.opengis.net/ows/1.1"
 xmlns:xlink="http://www.w3.org/1999/xlink"><Contents>
<Layer><ows:Title>Ortho</ows:Title><ows:Identifier>ortho</ows:Identifier><Style><ows:Identifier>default</ows:Identifier></Style>
<Format>image/jpeg</Format><TileMatrixSetLink><TileMatrixSet>EPSG:28992</TileMatrixSet></TileMatrixSetLink>
<ResourceURL format="image/jpeg" resourceType="tile" template="https://t/{TileMatrixSet}/{TileMatrix}/{TileCol}/{TileRow}.jpeg"/>
</Layer>
<TileMatrixSet><ows:Identifier>EPSG:28992</ows:Identifier><ows:SupportedCRS>urn:ogc:def:crs:EPSG::28992</ows:SupportedCRS>
<TileMatrix><ows:Identifier>0</ows:Identifier><ScaleDenominator>12288000</ScaleDenominator><TopLeftCorner>-285401.92 903401.92</TopLeftCorner>
<TileWidth>256</TileWidth><TileHeight>256</TileHeight><MatrixWidth>1</MatrixWidth><MatrixHeight>1</MatrixHeight></TileMatrix>
<TileMatrix><ows:Identifier>1</ows:Identifier><ScaleDenominator>6144000</ScaleDenominator><TopLeftCorner>-285401.92 903401.92</TopLeftCorner>
<TileWidth>256</TileWidth><TileHeight>256</TileHeight><MatrixWidth>2</MatrixWidth><MatrixHeight>2</MatrixHeight></TileMatrix>
</TileMatrixSet></Contents></Capabilities>"""


def test_wms_capabilities():
    layers = wms.parse_capabilities(WMS_CAPS)
    assert [l.name for l in layers] == ["ortho"]
    assert layers[0].crs == ["EPSG:28992", "EPSG:3857"]
    assert layers[0].bbox_wgs84 == (53.6, 3.1, 50.5, 7.5)


def test_wms_axis_order():
    p = wms.build_getmap_params("a", (1, 2, 3, 4), 10, 10, "EPSG:4326", version="1.3.0")
    assert p["bbox"] == "2,1,4,3" and p["crs"] == "EPSG:4326"
    p = wms.build_getmap_params("a", (1, 2, 3, 4), 10, 10, "EPSG:28992", version="1.3.0")
    assert p["bbox"] == "1,2,3,4"
    p = wms.build_getmap_params("a", (1, 2, 3, 4), 10, 10, "EPSG:4326", version="1.1.1")
    assert p["bbox"] == "1,2,3,4" and p["srs"] == "EPSG:4326"


def test_crs_helpers():
    assert is_north_first("EPSG:4326") and not is_north_first("EPSG:3857")
    assert meters_per_unit("EPSG:28992") == 1.0
    assert meters_per_unit("EPSG:4326") == approx(111319.49, rel=1e-6)


def test_wmts_capabilities():
    caps = wmts.parse_capabilities(WMTS_CAPS)
    layer = caps.layers["ortho"]
    assert layer.resource_urls["image/jpeg"].startswith("https://t/")
    tms = wmts.choose_tile_matrix_set(caps, layer, crs="EPSG:28992")
    assert tms.crs == "EPSG:28992"
    assert tms.matrices[0].resolution == approx(3440.64)          # 12288000 * 0.28 mm
    assert tms.matrices[0].top_left == (-285401.92, 903401.92)
    assert wmts.choose_matrix(tms, None).identifier == "1"
    assert wmts.choose_matrix(tms, 3000).identifier == "1"
    assert wmts.choose_matrix(tms, 5000).identifier == "0"


def test_wcs_description():
    with open("services/data/ahn_describe.xml", "rb") as f:
        desc = wcs.parse_coverage_description(f.read(), "dsm_05m")
    assert desc.crs == "EPSG:28992"
    assert desc.axis_labels == ["x", "y"]
    assert desc.resolution == (0.5, 0.5)


def test_mosaic():
    calls = []

    async def fetch(bounds, w, h):
        calls.append((bounds, w, h))
        return np.full((1, h, w), len(calls), dtype=np.uint8), None

    array, nodata = asyncio.run(mosaic_async((1.0, 0, 0.0, 0, -1.0, 10.0), 5, 3, fetch, max_size=2))
    assert array.shape == (1, 3, 5)
    assert len(calls) == 6
    assert calls[0] == ((0.0, 8.0, 2.0, 10.0), 2, 2)


def test_pdok_extent():
    from pytest import raises
    from streetlevel.aerial.pdok import pdok
    pdok._check_extent(52.38, 4.88, 52.37, 4.90)            # Amsterdam: fine
    with raises(ValueError):
        pdok._check_extent(51.51, -0.13, 51.50, -0.12)      # London


def test_ea_coverage_lookup():
    from pytest import raises
    from streetlevel.elevation import ea
    ids = ["13787b9a__Lidar_Composite_Elevation_DTM_1m", "13787b9a__Lidar_Composite_Hillshade_DTM_1m"]
    assert ea._pick(ids, ea.DTM_SUFFIX, "u") == ids[0]
    with raises(ValueError):
        ea._pick(ids, ea.DSM_SUFFIX, "u")
