mirrorworld.ja: Já 360
====================================

Finding panoramas
-----------------
    .. autofunction:: mirrorworld.ja.find_panorama
    
    Usage sample::
    
      from mirrorworld import ja
      
      pano = ja.find_panorama(64.149726, -21.940347)
      print(pano.id)
      print(pano.lat, pano.lon)
      print(pano.heading)
      
    .. autofunction:: mirrorworld.ja.find_panorama_async
    
    Usage sample::
    
      from mirrorworld import ja
      from aiohttp import ClientSession
      
      async with ClientSession() as session:
          pano = await ja.find_panorama_async(64.149726, -21.940347, session)
          print(pano.id)
          print(pano.lat, pano.lon)
          print(pano.heading)
          
    .. autofunction:: mirrorworld.ja.find_panorama_by_id
    
    Usage sample::
    
      from mirrorworld import ja
      
      pano = ja.find_panorama_by_id(2962469)
      print(pano.lat, pano.lon)
      print(pano.date)
      print(pano.address)
       
    .. autofunction:: mirrorworld.ja.find_panorama_by_id_async
    
    Usage sample::
    
      from mirrorworld import ja
      from aiohttp import ClientSession
      
      async with ClientSession() as session:
          pano = await ja.find_panorama_by_id_async(2962469, session)
          print(pano.lat, pano.lon)
          print(pano.date)
          print(pano.address)


Downloading panoramas
---------------------
    .. autofunction:: mirrorworld.ja.get_panorama
    .. autofunction:: mirrorworld.ja.get_panorama_async
    .. autofunction:: mirrorworld.ja.download_panorama
    
    Usage sample::
    
      from mirrorworld import ja
  
      pano = ja.find_panorama_by_id(2962469)
      ja.download_panorama(pano, f"{pano.id}.jpg")
     
    .. autofunction:: mirrorworld.ja.download_panorama_async
    
    Usage sample::
    
      from mirrorworld import ja
      from aiohttp import ClientSession
      
      async with ClientSession() as session:
          pano = await ja.find_panorama_by_id_async(2962469, session)
          await ja.download_panorama_async(pano, f"{pano.id}.jpg", session)

Data classes
----------------------
    .. autoclass:: mirrorworld.ja.panorama.Address
      :members:
    .. autoclass:: mirrorworld.ja.panorama.CaptureDate
      :members:
    .. autoclass:: mirrorworld.ja.panorama.JaPanorama
      :members:

Miscellaneous
-------------
    .. autofunction:: mirrorworld.ja.build_permalink
