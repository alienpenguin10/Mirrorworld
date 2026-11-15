# Mirrorworld addition (not in upstream streetlevel).
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple

import numpy as np


@dataclass
class MapFeature:
    """
    An object that Mapillary detected in several images and triangulated to a map position, e.g. a utility
    pole, manhole, junction box, street light, fire hydrant or traffic sign.

    The full list of values is at https://www.mapillary.com/developer/api-documentation/points and
    https://www.mapillary.com/developer/api-documentation/traffic-signs.
    """

    id: int
    """The map feature ID."""
    lat: float
    """Latitude of the triangulated position."""
    lon: float
    """Longitude of the triangulated position."""
    value: str
    """Object class, e.g. ``object--support--utility-pole`` or ``regulatory--stop--g1``."""
    layer: str
    """``point`` or ``traffic_sign``."""
    first_seen: Optional[datetime] = None
    """Capture time of the earliest image showing the object."""
    last_seen: Optional[datetime] = None
    """Capture time of the latest image showing the object."""
    aligned_direction: Optional[float] = None
    """Facing direction in radians (traffic signs), from :func:`find_map_feature_by_id`."""
    image_ids: Optional[List[int]] = None
    """IDs of the images in which the object was detected, from :func:`find_map_feature_by_id`."""
    distance: Optional[float] = None
    """Distance from the search point in meters (only set by :func:`find_map_features`)."""


@dataclass
class Detection:
    """A segmentation of one object in one image."""

    id: int
    """The detection ID."""
    value: str
    """Object or surface class, e.g. ``construction--flat--sidewalk`` or ``object--manhole``."""
    polygons: List[List[List[Tuple[float, float]]]]
    """Polygons, each a list of rings, each a list of (x, y) points normalized to 0..1 of the image width and
    height with the origin at the top left. The first ring of a polygon is its outline; further rings are holes.
    For 360° panoramas the coordinates refer to the equirectangular image."""
    created_at: Optional[datetime] = None
    """When Mapillary created the detection."""


@dataclass
class PointCloud:
    """
    Points of a Mapillary structure-from-motion reconstruction (OpenSfM), in a local east/north/up frame
    centered on ``reference``.
    """

    xyz: np.ndarray
    """(N, 3) east, north, up coordinates in meters relative to ``reference``."""
    rgb: np.ndarray
    """(N, 3) colors, 0..255."""
    reference: Tuple[float, float, float]
    """Latitude, longitude and altitude of the local frame's origin."""
    reconstruction: dict = field(repr=False, default_factory=dict)
    """The full OpenSfM reconstruction (cameras, shots with poses, points)."""

    def to_wgs84(self) -> np.ndarray:
        """
        Converts the points to geographic coordinates.

        :return: (N, 3) latitude, longitude and ellipsoidal height.
        """
        from pyproj import Transformer
        lat0, lon0, alt0 = self.reference
        transformer = Transformer.from_pipeline(
            f"+proj=pipeline +step +inv +proj=topocentric +ellps=WGS84 +lat_0={lat0} +lon_0={lon0} +h_0={alt0} "
            f"+step +inv +proj=cart +ellps=WGS84")
        lon, lat, h = transformer.transform(self.xyz[:, 0], self.xyz[:, 1], self.xyz[:, 2])
        return np.column_stack([lat, lon, h])
