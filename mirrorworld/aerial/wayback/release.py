# Mirrorworld addition (not in upstream streetlevel).
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class WaybackRelease:
    """One archived release of Esri World Imagery."""

    id: int
    """Release number, used in tile URLs. Not chronological; sort by ``date``."""
    date: date
    """Publication date of the release."""
    title: str
    """Title, e.g. ``World Imagery (Wayback 2026-10-29)``."""
    tile_url_template: str
    """Tile URL with ``{level}``, ``{row}`` and ``{col}`` placeholders."""
    metadata_url: Optional[str] = None
    """ArcGIS MapServer with the capture metadata of this release."""


@dataclass
class WaybackVersion:
    """A distinct version of the imagery at one location, i.e. the release that introduced it."""

    release: WaybackRelease
    """The release in which this imagery first appeared."""
    capture_date: Optional[date] = None
    """Acquisition date of the imagery, from the release metadata."""
    resolution: Optional[float] = None
    """Source resolution in meters."""
    accuracy: Optional[float] = None
    """Reported horizontal accuracy in meters."""
    source: Optional[str] = None
    """Imagery product name, e.g. ``Vivid Advanced``."""
    provider: Optional[str] = None
    """Imagery vendor, e.g. ``Vantor`` or a local government."""
