# Mirrorworld addition (not in upstream streetlevel).
import math
from datetime import datetime
from typing import List, Optional

from .panorama import PanoramaxPanorama


def parse_feature_collection(response: dict) -> List[PanoramaxPanorama]:
    return [parse_panorama(feature) for feature in response.get("features", [])]


def get_next_link(response: dict) -> Optional[str]:
    for link in response.get("links", []):
        if link.get("rel") == "next":
            return link.get("href")
    return None


def parse_panorama(feature: dict) -> PanoramaxPanorama:
    lon, lat = feature["geometry"]["coordinates"][:2]
    props = feature.get("properties", {})
    interior = props.get("pers:interior_orientation") or {}
    dims = interior.get("sensor_array_dimensions") or [None, None]
    links = {link.get("rel"): link.get("href", "") for link in feature.get("links", [])}
    providers = feature.get("providers") or []
    return PanoramaxPanorama(
        id=feature["id"],
        lat=lat,
        lon=lon,
        date=_parse_datetime(props.get("datetimetz") or props.get("datetime")),
        heading=_radians(props.get("view:azimuth")),
        pitch=_radians(props.get("pers:pitch")),
        roll=_radians(props.get("pers:roll")),
        sequence_id=feature.get("collection"),
        rank_in_sequence=props.get("geovisio:rank_in_collection"),
        previous_id=_last_path_part(links.get("prev")),
        next_id=_last_path_part(links.get("next")),
        field_of_view=interior.get("field_of_view"),
        make=interior.get("camera_manufacturer"),
        model=interior.get("camera_model"),
        width=dims[0],
        height=dims[1],
        horizontal_accuracy=props.get("quality:horizontal_accuracy"),
        producer=props.get("geovisio:producer") or (providers[0].get("name") if providers else None),
        license=props.get("license"),
        instance=links.get("via"),
        image_urls={key: asset["href"] for key, asset in (feature.get("assets") or {}).items() if "href" in asset}
        or None,
    )


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _radians(value) -> Optional[float]:
    return math.radians(value) if value is not None else None


def _last_path_part(url: Optional[str]) -> Optional[str]:
    return url.rstrip("/").split("/")[-1] if url else None
