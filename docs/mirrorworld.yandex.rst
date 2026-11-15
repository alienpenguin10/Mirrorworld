mirrorworld.yandex: Yandex Panorama
===================================

Finding panoramas
-----------------
    .. autofunction:: mirrorworld.yandex.find_panorama
    
    Usage sample::
    
      from mirrorworld import yandex

      pano = yandex.find_panorama(43.249064, 76.941999)
      print(pano.lat, pano.lon)
      print(pano.id)
      print(pano.date)
    
    .. autofunction:: mirrorworld.yandex.find_panorama_async
    
    Usage sample::
    
      from mirrorworld import yandex
      from aiohttp import ClientSession
      
      async with ClientSession() as session:
          pano = await yandex.find_panorama_async(43.249064, 76.941999, session)
          print(pano.lat, pano.lon)
          print(pano.id)
          print(pano.date)
     
    .. autofunction:: mirrorworld.yandex.find_panorama_by_id
    
    Usage sample::
    
      from mirrorworld import yandex
  
      pano = yandex.find_panorama_by_id("1532719828_788624743_23_1678861237")
      print(pano.lat, pano.lon)
      print(pano.date)
      print(pano.heading)
      
    .. autofunction:: mirrorworld.yandex.find_panorama_by_id_async
    
    Usage sample::
    
      from mirrorworld import yandex
      from aiohttp import ClientSession
      
      async with ClientSession() as session:
          pano = await yandex.find_panorama_by_id_async("1532719828_788624743_23_1678861237", session)
          print(pano.lat, pano.lon)
          print(pano.date)
          print(pano.heading)

Downloading panoramas
---------------------
    .. autofunction:: mirrorworld.yandex.get_panorama
    .. autofunction:: mirrorworld.yandex.get_panorama_async
    .. autofunction:: mirrorworld.yandex.download_panorama
    
    Usage sample::
    
      from mirrorworld import yandex
  
      pano = yandex.find_panorama_by_id("1532719828_788624743_23_1678861237")
      yandex.download_panorama(pano, f"{pano.id}.jpg")
    
    .. autofunction:: mirrorworld.yandex.download_panorama_async
    
    Usage sample::
    
      from mirrorworld import yandex
      from aiohttp import ClientSession
      
      async with ClientSession() as session:
          pano = await yandex.find_panorama_by_id_async("1532719828_788624743_23_1678861237", session)
          await yandex.download_panorama_async(pano, f"{pano.id}.jpg", session)

Data classes
------------
    .. autoclass:: mirrorworld.yandex.panorama.Address
      :members:
    .. autoclass:: mirrorworld.yandex.panorama.Marker
      :members:
    .. autoclass:: mirrorworld.yandex.panorama.Place
      :members:
    .. autoclass:: mirrorworld.yandex.panorama.YandexPanorama
      :members:

Miscellaneous
-------------
    .. autofunction:: mirrorworld.yandex.build_permalink