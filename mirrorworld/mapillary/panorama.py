# Mirrorworld addition (not in upstream streetlevel).
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

from .util import build_permalink


@dataclass
class MapillaryPanorama:
    """
    Metadata of a Mapillary image.

    Mapillary hosts both 360° panoramas and ordinary (perspective) photos; ``is_pano`` tells them apart.
    The class is named like the other providers' for consistency.

    ID, latitude and longitude are always present. Coverage tiles provide the fields up to
    ``quality_score``; :func:`mirrorworld.mapillary.find_panorama_by_id` fills in the rest.
    """

    id: int
    """The image ID."""
    lat: float
    """Latitude as recorded by the camera."""
    lon: float
    """Longitude as recorded by the camera."""

    date: Optional[datetime] = None
    """Capture time (UTC)."""
    heading: Optional[float] = None
    """Heading in radians as recorded by the camera, where 0 is north and π/2 is east."""
    is_pano: Optional[bool] = None
    """Whether this is a 360° panorama."""
    sequence_id: Optional[str] = None
    """ID of the sequence this image belongs to."""
    creator_id: Optional[int] = None
    """ID of the uploader."""
    organization_id: Optional[int] = None
    """ID of the organization that uploaded the image, if any."""
    quality_score: Optional[float] = None
    """Mapillary's image quality score from 0 to 1."""

    computed_lat: Optional[float] = None
    """Latitude after Mapillary's structure-from-motion correction."""
    computed_lon: Optional[float] = None
    """Longitude after Mapillary's structure-from-motion correction."""
    computed_heading: Optional[float] = None
    """Heading in radians after Mapillary's correction."""
    elevation: Optional[float] = None
    """Altitude in meters as recorded by the camera."""
    computed_elevation: Optional[float] = None
    """Altitude in meters after Mapillary's correction."""

    camera_type: Optional[str] = None
    """Projection: ``perspective``, ``fisheye``, ``equirectangular`` or ``spherical``."""
    camera_parameters: Optional[list] = None
    """Intrinsics, e.g. focal length and radial distortion for perspective cameras."""
    make: Optional[str] = None
    """Camera make."""
    model: Optional[str] = None
    """Camera model."""
    width: Optional[int] = None
    """Width of the original image in pixels."""
    height: Optional[int] = None
    """Height of the original image in pixels."""
    creator_username: Optional[str] = None
    """User name of the uploader."""

    image_urls: Optional[Dict[str, str]] = None
    """Signed image URLs by size: ``256``, ``1024``, ``2048`` and ``original``. They expire after a while."""

    @property
    def is_equirectangular(self) -> bool:
        return bool(self.is_pano) or self.camera_type in ("equirectangular", "spherical")

    @property
    def permalink(self) -> str:
        """A link to this image on mapillary.com."""
        return build_permalink(id=self.id, lat=self.lat, lon=self.lon)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return f"{self.id} ({self.lat:.6f}, {self.lon:.6f}) [{self.date}]"
