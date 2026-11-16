mirrorworld.streetside: Bing Streetside
=======================================


Finding panoramas
-----------------
    .. autofunction:: mirrorworld.streetside.find_panoramas
    
    Usage sample::
    
      from mirrorworld import streetside
      
      panos = streetside.find_panoramas(-17.831848, 31.046641)
      print(panos[0].lat, panos[0].lon)
      print(panos[0].id)
      print(panos[0].date)
    
    .. autofunction:: mirrorworld.streetside.find_panoramas_async
    
    Usage sample::
    
      from mirrorworld import streetside
      from aiohttp import ClientSession
      
      async with ClientSession() as session:
          panos = await streetside.find_panoramas_async(-17.831848, 31.046641, session)
          print(panos[0].lat, panos[0].lon)
          print(panos[0].id)
          print(panos[0].date)
          
    .. autofunction:: mirrorworld.streetside.find_panoramas_in_bbox
    .. autofunction:: mirrorworld.streetside.find_panoramas_in_bbox_async
    .. autofunction:: mirrorworld.streetside.find_panorama_by_id
    
    Usage sample::
    
      from mirrorworld import streetside
  
      pano = streetside.find_panorama_by_id(398611371)
      print(pano.lat, pano.lon)
      print(pano.date)
      print(pano.heading)

    .. autofunction:: mirrorworld.streetside.find_panorama_by_id_async
    
    Usage sample::
    
      from mirrorworld import streetside
      from aiohttp import ClientSession
      
      async with ClientSession() as session:
          pano = await streetside.find_panorama_by_id_async(398611371, session)
          print(pano.lat, pano.lon)
          print(pano.date)
          print(pano.heading)

Downloading panoramas
---------------------
    .. autofunction:: mirrorworld.streetside.get_panorama
    .. autofunction:: mirrorworld.streetside.get_panorama_async
    .. autofunction:: mirrorworld.streetside.download_panorama
    
    Usage sample::
    
      from mirrorworld import streetside
  
      pano = streetside.find_panorama_by_id(398611371)
      streetside.download_panorama(pano, f"{pano.id}.jpg")
    
    .. autofunction:: mirrorworld.streetside.download_panorama_async
    
    Usage sample::
    
      from mirrorworld import streetside
      from aiohttp import ClientSession
      
      async with ClientSession() as session:
          pano = await streetside.find_panorama_by_id_async(398611371, session)
          await streetside.download_panorama_async(pano, f"{pano.id}.jpg", session)

Data classes
------------
    .. autoclass:: mirrorworld.streetside.panorama.StreetsidePanorama
      :members:

Miscellaneous
-------------
    .. autofunction:: mirrorworld.streetside.build_permalink
    .. autofunction:: mirrorworld.streetside.util.from_base4
    .. autofunction:: mirrorworld.streetside.util.to_base4
