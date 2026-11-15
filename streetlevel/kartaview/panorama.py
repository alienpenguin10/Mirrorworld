# Mirrorworld addition (not in upstream streetlevel).
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from .util import build_permalink


@dataclass
class KartaViewPanorama:
    """
    Metadata of a KartaView photo.

    KartaView (formerly OpenStreetCam) hosts both 360° panoramas and ordinary dashcam/phone photos;
    ``is_equirectangular`` tells them apart. The class is named like the other providers' for consistency.
    """

    id: int
    """The photo ID."""
    lat: float
    """Latitude as recorded by the device."""
    lon: float
    """Longitude as recorded by the device."""

    date: Optional[datetime] = None
    """Capture time (device local time as reported by the API)."""
    heading: Optional[float] = None
    """Heading in radians, where 0 is north and π/2 is east."""
    sequence_id: Optional[int] = None
    """ID of the sequence (track) the photo belongs to."""
    sequence_index: Optional[int] = None
    """Position of the photo in its sequence."""

    field_of_view: Optional[int] = None
    """Horizontal field of view in degrees as reported; 360 for panoramas, often 0 (unknown) otherwise."""
    projection: Optional[str] = None
    """Projection: ``PLANE`` for ordinary photos, ``SPHERE`` for 360° panoramas."""
    width: Optional[int] = None
    """Width of the full-size image in pixels."""
    height: Optional[int] = None
    """Height of the full-size image in pixels."""

    matched_lat: Optional[float] = None
    """Latitude snapped to the matched OSM way."""
    matched_lon: Optional[float] = None
    """Longitude snapped to the matched OSM way."""
    way_id: Optional[int] = None
    """ID of the OSM way the photo was matched to, if any."""
    gps_accuracy: Optional[float] = None
    """Reported GPS accuracy in meters."""
    distance: Optional[float] = None
    """Distance from the search point in meters (only set by :func:`find_panoramas`)."""

    image_urls: Optional[Dict[str, List[str]]] = None
    """Candidate URLs by size (``full``, ``large``, ``small``): the original storage file first, then the CDN
    copy (same pixel size, re-encoded), which is used when a storage host fails."""

    @property
    def is_equirectangular(self) -> bool:
        return self.projection == "SPHERE" or self.field_of_view == 360

    @property
    def permalink(self) -> str:
        """A link to this photo on kartaview.org."""
        return build_permalink(self.sequence_id, self.sequence_index or 0)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return f"{self.id} ({self.lat:.6f}, {self.lon:.6f}) [{self.date}]"
