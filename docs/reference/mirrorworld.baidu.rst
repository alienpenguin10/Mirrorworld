mirrorworld.baidu: Baidu Panorama
=================================

Support for Baidu Panorama of Baidu Maps, covering many cities in the PRC. 

``find_panorama`` accepts WGS84, GCJ-02, BD09, or BD09MC. The positions of retrieved panoramas
are given as WGS84, GJC-02, and BD09MC.

Finding panoramas
-----------------
    .. autofunction:: mirrorworld.baidu.find_panorama
    
    Usage sample::
    
      from mirrorworld import baidu
      
      pano = baidu.find_panorama(22.2937592, 114.1692527)
      print(pano.id)
      print(pano.lat, pano.lon)
      print(pano.date)
      
    .. autofunction:: mirrorworld.baidu.find_panorama_async
    
    Usage sample::
    
      from mirrorworld import baidu
      from aiohttp import ClientSession
      
      async with ClientSession() as session:
          pano = await baidu.find_panorama_async(22.2937592, 114.1692527, session)
          print(pano.id)
          print(pano.lat, pano.lon)
          print(pano.heading)
          
    .. autofunction:: mirrorworld.baidu.find_panorama_by_id
    
    Usage sample::
    
      from mirrorworld import baidu
      
      pano = baidu.find_panorama_by_id("09024200121707301421572809B")
      print(pano.lat, pano.lon)
      print(pano.date)
       
    .. autofunction:: mirrorworld.baidu.find_panorama_by_id_async
    
    Usage sample::
    
      from mirrorworld import baidu
      from aiohttp import ClientSession
      
      async with ClientSession() as session:
          pano = await baidu.find_panorama_by_id_async("09024200121707301421572809B", session)
          print(pano.lat, pano.lon)
          print(pano.date)
          
    .. autofunction:: mirrorworld.baidu.get_inter_metadata
    
    Usage sample::
    
      from mirrorworld import baidu
      
      inter = baidu.get_inter_metadata("b60ec15c48587562843304bc")
      print(inter.name)
      print(inter.lat, inter.lon)
      for floor in inter.floors:
          print(floor.number, [p.id for p in floor.panos])
    
    .. autofunction:: mirrorworld.baidu.get_inter_metadata_async
    
    Usage sample::
    
      from mirrorworld import baidu
      
      async with ClientSession() as session:
          inter = await baidu.get_inter_metadata_async("b60ec15c48587562843304bc", session)
          print(inter.name)
          print(inter.lat, inter.lon)
          for floor in inter.floors:
              print(floor.number, [p.id for p in floor.panos])


Downloading panoramas
---------------------
    .. autofunction:: mirrorworld.baidu.get_panorama
    .. autofunction:: mirrorworld.baidu.get_panorama_async
    .. autofunction:: mirrorworld.baidu.download_panorama
    
    Usage sample::
    
      from mirrorworld import baidu
  
      pano = baidu.find_panorama_by_id("09024200121707301421572809B")
      baidu.download_panorama(pano, f"{pano.id}.jpg")
     
    .. autofunction:: mirrorworld.baidu.download_panorama_async
    
    Usage sample::
    
      from mirrorworld import baidu
      from aiohttp import ClientSession
      
      async with ClientSession() as session:
          pano = await baidu.find_panorama_by_id_async("09024200121707301421572809B", session)
          await baidu.download_panorama_async(pano, f"{pano.id}.jpg", session)


Data classes and Enums
----------------------
    .. autoclass:: mirrorworld.baidu.Crs
      :members:
      :member-order: bysource
    .. autoclass:: mirrorworld.baidu.panorama.BaiduPanorama
      :members:
    .. autoclass:: mirrorworld.baidu.panorama.Floor
      :members:
    .. autoclass:: mirrorworld.baidu.panorama.InteriorMetadata
      :members:
    .. autoclass:: mirrorworld.baidu.panorama.InteriorPoint
      :members:
    .. autoclass:: mirrorworld.baidu.panorama.PanoInteriorMetadata
      :members:
    .. autoclass:: mirrorworld.baidu.panorama.PanoInteriorPoint
      :members:
    .. autoclass:: mirrorworld.baidu.panorama.Provider
      :members:
    .. autoclass:: mirrorworld.baidu.panorama.User
      :members:

Miscellaneous
-------------
    .. autofunction:: mirrorworld.baidu.build_permalink
