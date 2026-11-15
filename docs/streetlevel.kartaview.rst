streetlevel.kartaview: KartaView
================================

KartaView (formerly OpenStreetCam) has a public API that needs no key. Imagery is CC BY-SA 4.0.
Photos can be 360° panoramas or ordinary dashcam/phone photos (``is_equirectangular``).
Downloads try the original file first and fall back to KartaView's CDN copy when a storage host fails.

Finding photos
--------------
    .. autofunction:: streetlevel.kartaview.find_panoramas
    .. autofunction:: streetlevel.kartaview.find_panoramas_async
    .. autofunction:: streetlevel.kartaview.find_panorama_by_id
    .. autofunction:: streetlevel.kartaview.find_panorama_by_id_async
    .. autofunction:: streetlevel.kartaview.get_sequence
    .. autofunction:: streetlevel.kartaview.get_sequence_async

    Usage sample::

      from streetlevel import kartaview

      panos = kartaview.find_panoramas(47.6062, -122.3321, radius=100)
      print(panos[0].distance, panos[0].date, panos[0].permalink)
      kartaview.download_panorama(panos[0], f"{panos[0].id}.jpg")

    Async::

      from streetlevel import kartaview
      from aiohttp import ClientSession

      async with ClientSession() as session:
          panos = await kartaview.find_panoramas_async(47.6062, -122.3321, session, radius=100)
          await kartaview.download_panorama_async(panos[0], f"{panos[0].id}.jpg", session)


Downloading photos
------------------
    .. autofunction:: streetlevel.kartaview.get_panorama
    .. autofunction:: streetlevel.kartaview.get_panorama_async
    .. autofunction:: streetlevel.kartaview.download_panorama
    .. autofunction:: streetlevel.kartaview.download_panorama_async

Data classes
------------
    .. autoclass:: streetlevel.kartaview.panorama.KartaViewPanorama
      :members:

Miscellaneous
-------------
    .. autofunction:: streetlevel.kartaview.build_permalink
