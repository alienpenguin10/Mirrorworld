mirrorworld.mapy: Mapy.cz Panorama
=======================================

Finding panoramas
-----------------
    .. autofunction:: mirrorworld.mapy.find_panorama
    
    Usage sample::
    
      from mirrorworld import mapy
  
      pano = mapy.find_panorama(50.704732, 14.404809)
      print(pano.lat, pano.lon)
      print(pano.id)
      print(pano.date)

    .. autofunction:: mirrorworld.mapy.find_panorama_async
    
    Usage sample::
    
      from mirrorworld import mapy
      from aiohttp import ClientSession
      
      async with ClientSession() as session:
          pano = await mapy.find_panorama_async(50.704732, 14.404809, session)
          print(pano.lat, pano.lon)
          print(pano.id)
          print(pano.date)
          
    .. autofunction:: mirrorworld.mapy.find_panorama_by_id
    
    Usage sample::
    
      from mirrorworld import mapy
      
      pano = mapy.find_panorama_by_id(82102772)
      print(pano.lat, pano.lon)
      print(pano.date)
      print(pano.heading)

    .. autofunction:: mirrorworld.mapy.find_panorama_by_id_async
    
    Usage sample::
    
      from mirrorworld import mapy
      from aiohttp import ClientSession
      
      async with ClientSession() as session:
          pano = await mapy.find_panorama_by_id_async(82102772, session)
          print(pano.lat, pano.lon)
          print(pano.date)
          print(pano.heading)
    
    .. autofunction:: mirrorworld.mapy.get_links
    .. autofunction:: mirrorworld.mapy.get_links_async

Downloading panoramas
---------------------
    .. autofunction:: mirrorworld.mapy.get_panorama
    .. autofunction:: mirrorworld.mapy.get_panorama_async
    .. autofunction:: mirrorworld.mapy.download_panorama
    
    Usage sample::
    
      from mirrorworld import mapy
      
      pano = mapy.find_panorama_by_id(82102772)
      mapy.download_panorama(pano, f"{pano.id}.jpg")
      
    .. autofunction:: mirrorworld.mapy.download_panorama_async
    
    Usage sample::
    
      from mirrorworld import mapy
      from aiohttp import ClientSession
      
      async with ClientSession() as session:
          pano = await mapy.find_panorama_by_id_async(82102772, session)
          await mapy.download_panorama_async(pano, f"{pano.id}.jpg", session)

Data classes
------------
    .. autoclass:: mirrorworld.mapy.panorama.MapyPanorama
      :members:

Miscellaneous
-------------
    .. autofunction:: mirrorworld.mapy.build_permalink
