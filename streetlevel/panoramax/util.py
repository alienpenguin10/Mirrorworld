# Mirrorworld addition (not in upstream streetlevel).
DEFAULT_API_URL = "https://api.panoramax.xyz/api"
"""The federated catalogue, which indexes the public Panoramax instances (OSM France, IGN, ...)."""


def build_permalink(id: str, lat: float = None, lon: float = None, zoom: float = 18.0) -> str:
    """
    Creates a link to a picture in the Panoramax viewer.

    :param id: The picture ID (a UUID).
    :param lat: *(optional)* Latitude of the map center.
    :param lon: *(optional)* Longitude of the map center.
    :param zoom: *(optional)* Zoom level of the map. Defaults to 18.
    :return: A Panoramax URL.
    """
    url = f"https://api.panoramax.xyz/#focus=pic&pic={id}"
    if lat is not None and lon is not None:
        url += f"&map={zoom}/{lat}/{lon}"
    return url
