# Mirrorworld addition (not in upstream streetlevel).
import os

TOKEN_ENV_VAR = "MAPILLARY_ACCESS_TOKEN"


def build_permalink(id: int = None, lat: float = None, lon: float = None, zoom: float = 17.0) -> str:
    """
    Creates a link to an image, or to a location, on mapillary.com.

    :param id: *(optional)* The image ID.
    :param lat: *(optional)* Latitude of the map center.
    :param lon: *(optional)* Longitude of the map center.
    :param zoom: *(optional)* Zoom level of the map. Defaults to 17.
    :return: A Mapillary URL.
    """
    if id is None and (lat is None or lon is None):
        raise ValueError("You must pass an image ID, or a location, or both.")
    params = []
    if lat is not None and lon is not None:
        params += [f"lat={lat}", f"lng={lon}", f"z={zoom}"]
    if id is not None:
        params.append(f"pKey={id}")
    return "https://www.mapillary.com/app/?" + "&".join(params)


def get_access_token(access_token: str = None) -> str:
    """
    Returns the access token to use for Mapillary requests: the one passed in, or else the
    ``MAPILLARY_ACCESS_TOKEN`` environment variable. Tokens (``MLY|...``) are free from
    https://www.mapillary.com/dashboard/developers.

    :param access_token: *(optional)* An explicit token.
    :return: The token.
    """
    token = access_token or os.environ.get(TOKEN_ENV_VAR)
    if not token:
        raise ValueError(f"Mapillary requires an access token: pass access_token= or set {TOKEN_ENV_VAR}")
    return token
