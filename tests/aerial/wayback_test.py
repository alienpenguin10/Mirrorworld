# Mirrorworld addition (not in upstream streetlevel). Offline: no network requests.
from datetime import date

from streetlevel.aerial import wayback
import streetlevel.aerial.wayback.wayback as wb
import streetlevel.aerial.wayback.api as wb_api


def test_parse_config():
    config = {
        "10": {"itemTitle": "World Imagery (Wayback 2014-02-20)", "itemURL": "https://x/tile/10/{level}/{row}/{col}"},
        "43291": {"itemTitle": "World Imagery (Wayback 2026-10-29)", "itemURL": "https://x/tile/43291/{level}/{row}/{col}",
                  "metadataLayerUrl": "https://m/MapServer"},
        "junk": {"itemTitle": "no date"},
    }
    releases = wayback.parse_config(config)
    assert [r.id for r in releases] == [43291, 10]
    assert releases[0].date == date(2026, 10, 29)
    assert releases[0].metadata_url == "https://m/MapServer"
    assert releases[1].tile_url_template.format(level=19, row=2, col=3) == "https://x/tile/10/19/2/3"


def test_metadata_layer_per_zoom():
    assert wb_api.build_metadata_query_url("https://m/MapServer", 19) == "https://m/MapServer/4/query"
    assert wb_api.build_metadata_query_url("https://m/MapServer", 23) == "https://m/MapServer/0/query"
    assert wb_api.build_metadata_query_url("https://m/MapServer", 3) == "https://m/MapServer/13/query"


def test_parse_date():
    assert wb._parse_yyyymmdd(20250505) == date(2025, 5, 5)
    assert wb._parse_yyyymmdd(None) is None


def test_merge_versions():
    from streetlevel.aerial.wayback.release import WaybackRelease, WaybackVersion

    def version(release_day, capture, source="Vivid"):
        release = WaybackRelease(id=release_day, date=date(2025, 1, release_day), title="t", tile_url_template="u")
        return WaybackVersion(release=release, capture_date=capture, resolution=0.3, source=source)

    newest_first = [version(30, date(2024, 6, 1)), version(20, date(2020, 4, 22)), version(15, date(2020, 4, 22)),
                    version(10, date(2020, 4, 22)), version(5, None), version(4, None)]
    merged = wayback.merge_versions(newest_first)
    assert [v.release.id for v in merged] == [30, 10, 5, 4]   # oldest release of a repeated capture is kept
