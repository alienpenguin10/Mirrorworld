# SURVAI: added module (not upstream).
def build_permalink(lat: float, lon: float, zoom: int = 18) -> str:
    """
    Creates a link to Esri World Imagery Wayback, which shows the current World Imagery
    and its earlier releases, at a location.

    :param lat: Latitude.
    :param lon: Longitude.
    :param zoom: *(optional)* Zoom level. Defaults to 18.
    :return: A Wayback URL.
    """
    return f"https://livingatlas.arcgis.com/wayback/#mapCenter={lon}%2C{lat}%2C{zoom}"
