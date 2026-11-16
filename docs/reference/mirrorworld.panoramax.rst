mirrorworld.panoramax: Panoramax
================================

Panoramax, the federated open street-level imagery platform (mostly CC BY-SA 4.0). No key. The federated
catalogue ``api.panoramax.xyz`` is queried by default; pass ``api_url=`` for one instance.

Finding pictures
----------------
    .. autofunction:: mirrorworld.panoramax.find_panoramas
    .. autofunction:: mirrorworld.panoramax.find_panoramas_async
    .. autofunction:: mirrorworld.panoramax.find_panoramas_in_bbox
    .. autofunction:: mirrorworld.panoramax.find_panoramas_in_bbox_async
    .. autofunction:: mirrorworld.panoramax.find_panorama_by_id
    .. autofunction:: mirrorworld.panoramax.find_panorama_by_id_async
    .. autofunction:: mirrorworld.panoramax.get_sequence
    .. autofunction:: mirrorworld.panoramax.get_sequence_async

    Usage sample::

      from mirrorworld import panoramax

      pics = panoramax.find_panoramas(51.5088, -0.127, radius=30)
      print(pics[0].distance, pics[0].date, pics[0].is_equirectangular, pics[0].permalink)


Downloading pictures
--------------------
    .. autofunction:: mirrorworld.panoramax.get_panorama
    .. autofunction:: mirrorworld.panoramax.get_panorama_async
    .. autofunction:: mirrorworld.panoramax.download_panorama
    .. autofunction:: mirrorworld.panoramax.download_panorama_async

    Usage sample::

      panoramax.download_panorama(pics[0], f"{pics[0].id}.jpg", size="hd")


Data classes
------------
    .. autoclass:: mirrorworld.panoramax.panorama.PanoramaxPanorama
      :members:

Miscellaneous
-------------
    .. autofunction:: mirrorworld.panoramax.build_permalink
