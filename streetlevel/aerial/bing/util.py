# SURVAI: added module (not upstream).
def to_quadkey(x: int, y: int, zoom: int) -> str:
    """
    Converts XYZ tile coordinates to a Bing Maps quadkey.

    :param x: X coordinate.
    :param y: Y coordinate.
    :param zoom: Zoom level.
    :return: The quadkey, which has one digit per zoom level.
    """
    digits = []
    for i in range(zoom, 0, -1):
        mask = 1 << (i - 1)
        digits.append(str((1 if x & mask else 0) + (2 if y & mask else 0)))
    return "".join(digits)


def from_quadkey(quadkey: str):
    """
    Converts a Bing Maps quadkey to XYZ tile coordinates.

    :param quadkey: The quadkey.
    :return: X, Y and zoom.
    """
    x = y = 0
    zoom = len(quadkey)
    for i, digit in enumerate(quadkey):
        mask = 1 << (zoom - i - 1)
        if digit in "13":
            x |= mask
        if digit in "23":
            y |= mask
    return x, y, zoom


def build_permalink(lat: float, lon: float, zoom: int = 18) -> str:
    """
    Creates a Bing Maps link showing aerial imagery at a location.

    :param lat: Latitude.
    :param lon: Longitude.
    :param zoom: *(optional)* Zoom level. Defaults to 18.
    :return: A Bing Maps URL.
    """
    return f"https://www.bing.com/maps?cp={lat}%7E{lon}&lvl={zoom}&style=a"
