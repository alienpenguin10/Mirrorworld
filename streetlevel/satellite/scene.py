# Mirrorworld addition (not in upstream streetlevel).
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Tuple


@dataclass
class Scene:
    """One item of a STAC catalogue, e.g. a satellite scene or an aerial survey tile."""

    id: str
    """Item ID."""
    collection: str
    """Collection ID, e.g. ``sentinel-2-l2a``."""
    datetime: Optional[datetime]
    """Acquisition time (UTC)."""
    bbox: Tuple[float, float, float, float]
    """Footprint bounding box as (west, south, east, north)."""
    endpoint: str
    """STAC API the item came from."""
    cloud_cover: Optional[float] = None
    """Cloud cover in percent, for optical scenes."""
    assets: Dict[str, dict] = field(default_factory=dict, repr=False)
    """Asset name -> STAC asset (``href``, ``type``, ``eo:bands``, ``raster:bands``, ...)."""
    properties: dict = field(default_factory=dict, repr=False)
    """All item properties."""

    def covers(self, north: float, west: float, south: float, east: float) -> bool:
        """Whether the footprint's bounding box contains a bounding box."""
        w, s, e, n = self.bbox
        return w <= west and s <= south and e >= east and n >= north
