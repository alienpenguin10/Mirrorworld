mirrorworld.naver: Naver Street View
====================================

Finding panoramas
-----------------
    .. autofunction:: mirrorworld.naver.find_panorama
    
    Usage sample::
    
      from mirrorworld import naver

      pano = naver.find_panorama(37.4481486, 126.4509719)
      print(pano.lat, pano.lon)
      print(pano.id)
      print(pano.date)
      
    .. autofunction:: mirrorworld.naver.find_panorama_async
    
    Usage sample::
    
      from mirrorworld import naver
      from aiohttp import ClientSession
      
      async with ClientSession() as session:
          pano = await naver.find_panorama_async(37.4481486, 126.4509719, session)
          print(pano.lat, pano.lon)
          print(pano.id)
          print(pano.date)
    
    .. autofunction:: mirrorworld.naver.find_panorama_by_id
    
    Usage sample::
    
      from mirrorworld import naver

      pano = naver.find_panorama_by_id("hQ46n55JstD9C-tGdzZz2g")
      print(pano.lat, pano.lon)
      print(pano.date)
      print(pano.heading)
      
    .. autofunction:: mirrorworld.naver.find_panorama_by_id_async
    
    Usage sample::
    
      from mirrorworld import naver
      from aiohttp import ClientSession
      
      async with ClientSession() as session:
          pano = await naver.find_panorama_by_id_async("hQ46n55JstD9C-tGdzZz2g", session)
          print(pano.lat, pano.lon)
          print(pano.date)
          print(pano.heading)
          
    .. autofunction:: mirrorworld.naver.get_depth
    .. autofunction:: mirrorworld.naver.get_depth_async
    .. autofunction:: mirrorworld.naver.get_historical
    .. autofunction:: mirrorworld.naver.get_historical_async
    .. autofunction:: mirrorworld.naver.get_neighbors
    .. autofunction:: mirrorworld.naver.get_neighbors_async
    

Downloading panoramas
---------------------
    .. autofunction:: mirrorworld.naver.get_panorama
    .. autofunction:: mirrorworld.naver.get_panorama_async
    .. autofunction:: mirrorworld.naver.download_panorama
    
    Usage sample::
    
      from mirrorworld import naver
  
      pano = naver.find_panorama_by_id("hQ46n55JstD9C-tGdzZz2g")
      naver.download_panorama(pano, f"{pano.id}.jpg")

    .. autofunction:: mirrorworld.naver.download_panorama_async
    
    Usage sample::
    
      from mirrorworld import naver
      from aiohttp import ClientSession
      
      async with ClientSession() as session:
          pano = await naver.find_panorama_by_id_async("hQ46n55JstD9C-tGdzZz2g", session)
          await naver.download_panorama_async(pano, f"{pano.id}.jpg", session)
          
    .. autofunction:: mirrorworld.naver.get_model
    .. autofunction:: mirrorworld.naver.get_model_async

Data classes and Enums
----------------------
    .. autoclass:: mirrorworld.naver.model.Model
      :members:
    .. autoclass:: mirrorworld.naver.panorama.NaverPanorama
      :members:
    .. autoclass:: mirrorworld.naver.panorama.Neighbors
      :members:
    .. autoclass:: mirrorworld.naver.panorama.Overlay
      :members:
    .. autoclass:: mirrorworld.naver.panorama.PanoramaType
      :members:
      :member-order: bysource

Miscellaneous
-------------
    .. autofunction:: mirrorworld.naver.build_permalink