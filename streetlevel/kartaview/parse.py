# Mirrorworld addition (not in upstream streetlevel).
import math
from datetime import datetime
from typing import List, Optional

from .panorama import KartaViewPanorama


def parse_panoramas(response: dict) -> List[KartaViewPanorama]:
    return [parse_panorama(photo) for photo in response["result"]["data"]]


def parse_panorama_response(response: dict) -> Optional[KartaViewPanorama]:
    data = (response.get("result") or {}).get("data")
    return parse_panorama(data) if data else None


def has_more_data(response: dict) -> bool:
    return bool((response.get("result") or {}).get("hasMoreData"))


def parse_panorama(photo: dict) -> KartaViewPanorama:
    return KartaViewPanorama(
        id=int(photo["id"]),
        lat=float(photo["lat"]),
        lon=float(photo["lng"]),
        date=_parse_date(photo.get("shotDate")),
        heading=_radians(photo.get("heading")),
        sequence_id=_int(photo.get("sequenceId")),
        sequence_index=_int(photo.get("sequenceIndex")),
        field_of_view=_int(photo.get("fieldOfView")),
        projection=photo.get("projection"),
        width=_int(photo.get("width")),
        height=_int(photo.get("height")),
        matched_lat=_float(photo.get("matchLat")),
        matched_lon=_float(photo.get("matchLng")),
        way_id=_int(photo.get("wayId")) or None,
        gps_accuracy=_float(photo.get("gpsAccuracy")),
        image_urls={
            "full": _urls(photo, "fileurlProc", "imageProcUrl"),
            "large": _urls(photo, "fileurlLTh", "imageLthUrl"),
            "small": _urls(photo, "fileurlTh", "imageThUrl"),
        },
    )


def _urls(photo: dict, *keys: str) -> List[str]:
    return [photo[key] for key in keys if photo.get(key)]


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    return None


def _float(value) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int(value) -> Optional[int]:
    number = _float(value)
    return int(number) if number is not None else None


def _radians(value) -> Optional[float]:
    number = _float(value)
    return math.radians(number) if number is not None else None
