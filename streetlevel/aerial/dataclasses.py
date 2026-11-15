# SURVAI: added module (not upstream).
from dataclasses import dataclass, field
from typing import List, Tuple

from PIL import Image


@dataclass
class AerialImage:
    """
    A stitched aerial image covering a bounding box, with the information needed to georeference it.

    The image is in Web Mercator (EPSG:3857). Its edges lie on pixel boundaries of the tile grid at ``zoom``,
    so ``north``/``west``/``south``/``east`` can differ from the requested box by less than one pixel.
    """

    image: Image.Image
    """The stitched image."""
    provider: str
    """Name of the imagery provider."""
    zoom: int
    """Zoom level of the tiles the image was stitched from."""

    north: float
    """Latitude of the top edge."""
    west: float
    """Longitude of the left edge."""
    south: float
    """Latitude of the bottom edge."""
    east: float
    """Longitude of the right edge."""

    origin_x: float
    """X coordinate of the top left corner in EPSG:3857 meters."""
    origin_y: float
    """Y coordinate of the top left corner in EPSG:3857 meters."""
    mercator_resolution: float
    """Pixel size in EPSG:3857 meters. Larger than the ground resolution away from the equator."""
    ground_resolution: float
    """Approximate pixel size on the ground in meters at the center of the image."""

    tile_count: int
    """Number of tiles the image was stitched from."""
    missing_tiles: List[Tuple[int, int]] = field(default_factory=list)
    """X/Y coordinates of tiles the provider has no imagery for at this zoom level. These areas are black."""
    metadata: dict = field(default_factory=dict)
    """Provider-specific metadata, e.g. capture date ranges reported by Bing."""
