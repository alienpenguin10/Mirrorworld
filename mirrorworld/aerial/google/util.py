# Mirrorworld addition (not in upstream streetlevel).
def build_permalink(lat: float, lon: float, zoom: int = 18) -> str:
    """
    Creates a Google Maps link showing satellite imagery at a location.

    :param lat: Latitude.
    :param lon: Longitude.
    :param zoom: *(optional)* Zoom level. Defaults to 18.
    :return: A Google Maps URL.
    """
    return f"https://www.google.com/maps/@{lat},{lon},{zoom}z/data=!3m1!1e3"
