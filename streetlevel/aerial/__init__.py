# SURVAI: added package (not upstream).
"""
Aerial and satellite orthoimagery from web map tile services.

One subpackage per provider, following the layout of the street-level providers
(``api.py`` builds and sends requests, ``<provider>.py`` holds the public functions,
``util.py`` holds provider-specific helpers). Shared tile math, stitching and saving
live in :mod:`streetlevel.aerial.util`.

Usage::

    from streetlevel.aerial import bing

    image = bing.get_image(47.6070, -122.3345, 47.6055, -122.3320, zoom=20)
    bing.download_image(47.6070, -122.3345, 47.6055, -122.3320, "seattle.jpg", zoom=20)
"""
