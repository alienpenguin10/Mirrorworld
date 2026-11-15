# Mirrorworld addition (not in upstream streetlevel).
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

from .util import build_permalink


@dataclass
class PanoramaxPanorama:
    """
    Metadata of a Panoramax picture.

    Panoramax hosts both 360° panoramas and ordinary photos; ``is_equirectangular`` tells them apart.
    The class is named like the other providers' for consistency.
    """

    id: str
    """The picture ID (a UUID)."""
    lat: float
    """Latitude."""
    lon: float
    """Longitude."""

    date: Optional[datetime] = None
    """Capture time (timezone-aware)."""
    heading: Optional[float] = None
    """Heading in radians, where 0 is north and π/2 is east."""
    pitch: Optional[float] = None
    """Pitch in radians."""
    roll: Optional[float] = None
    """Roll in radians."""
    sequence_id: Optional[str] = None
    """ID of the sequence (STAC collection) this picture belongs to."""
    rank_in_sequence: Optional[int] = None
    """Position of the picture in its sequence."""
    previous_id: Optional[str] = None
    """ID of the previous picture in the sequence."""
    next_id: Optional[str] = None
    """ID of the next picture in the sequence."""

    field_of_view: Optional[float] = None
    """Horizontal field of view in degrees; 360 for panoramas."""
    make: Optional[str] = None
    """Camera make."""
    model: Optional[str] = None
    """Camera model."""
    width: Optional[int] = None
    """Width of the original image in pixels."""
    height: Optional[int] = None
    """Height of the original image in pixels."""
    horizontal_accuracy: Optional[float] = None
    """Reported GPS accuracy in meters."""
    producer: Optional[str] = None
    """Name of the account that uploaded the picture."""
    license: Optional[str] = None
    """SPDX licence identifier, usually ``CC-BY-SA-4.0``."""
    instance: Optional[str] = None
    """Panoramax instance that hosts the picture."""
    distance: Optional[float] = None
    """Distance from the search point in meters (only set by :func:`find_panoramas`)."""

    image_urls: Optional[Dict[str, str]] = None
    """Image URLs by size: ``hd`` (original), ``sd`` and ``thumb``."""

    @property
    def is_equirectangular(self) -> bool:
        return self.field_of_view is not None and self.field_of_view >= 360

    @property
    def permalink(self) -> str:
        """A link to this picture in the Panoramax viewer."""
        return build_permalink(self.id, self.lat, self.lon)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return f"{self.id} ({self.lat:.6f}, {self.lon:.6f}) [{self.date}]"
