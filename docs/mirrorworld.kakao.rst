mirrorworld.kakao: Kakao Road View
===================================

Finding panoramas
-----------------
    .. autofunction:: mirrorworld.kakao.find_panoramas
    
    Usage sample::
    
      from mirrorworld import kakao
  
      panos = kakao.find_panoramas(37.4481486, 126.4509719)
      print(panos[0].lat, panos[0].lon)
      print(panos[0].id)
      print(panos[0].date)
    
    .. autofunction:: mirrorworld.kakao.find_panoramas_async
    
    Usage sample::
    
      from mirrorworld import kakao
      from aiohttp import ClientSession
      
      async with ClientSession() as session:
          panos = await kakao.find_panoramas_async(37.4481486, 126.4509719, session)
          print(panos[0].lat, panos[0].lon)
          print(panos[0].id)
          print(panos[0].date)
          
    .. autofunction:: mirrorworld.kakao.find_panorama_by_id
    
    Usage sample::
    
      from mirrorworld import kakao
  
      pano = kakao.find_panorama_by_id(1168949345)
      print(pano.lat, pano.lon)
      print(pano.date)
      print(pano.address)
    
    .. autofunction:: mirrorworld.kakao.find_panorama_by_id_async
    
    Usage sample::
    
      from mirrorworld import kakao
      from aiohttp import ClientSession
      
      async with ClientSession() as session:
          pano = await kakao.find_panorama_by_id_async(1168949345, session)
          print(pano.lat, pano.lon)
          print(pano.date)
          print(pano.address)

Downloading panoramas
---------------------
    .. autofunction:: mirrorworld.kakao.get_panorama
    .. autofunction:: mirrorworld.kakao.get_panorama_async
    .. autofunction:: mirrorworld.kakao.download_panorama
    
    Usage sample::
    
      from mirrorworld import kakao

      pano = kakao.find_panorama_by_id(1168949345)
      kakao.download_panorama(pano, f"{pano.id}.jpg")
      
    .. autofunction:: mirrorworld.kakao.download_panorama_async
    
    Usage sample::
    
      from mirrorworld import kakao
      from aiohttp import ClientSession
      
      async with ClientSession() as session:
          pano = await kakao.find_panorama_by_id_async(1168949345, session)
          await kakao.download_panorama(pano, f"{pano.id}.jpg")
    
    .. autofunction:: mirrorworld.kakao.get_depthmap
    .. autofunction:: mirrorworld.kakao.get_depthmap_async
    .. autofunction:: mirrorworld.kakao.download_depthmap
    .. autofunction:: mirrorworld.kakao.download_depthmap_async

Data classes and enums
----------------------
    .. autoclass:: mirrorworld.kakao.panorama.KakaoPanorama
      :members:
    .. autoclass:: mirrorworld.kakao.panorama.PanoramaType
      :members:
      :member-order: bysource

Miscellaneous
-------------
    .. autofunction:: mirrorworld.kakao.build_permalink
