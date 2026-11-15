mirrorworld.streetview: Google Street View
==========================================

Finding panoramas
-----------------
    .. autofunction:: mirrorworld.streetview.find_panorama
    
    Usage sample::
    
      from mirrorworld import streetview
      
      pano = streetview.find_panorama(45.59395, 24.631609)
      print(pano.id)
      print(pano.lat, pano.lon)
      print(pano.date)

    .. autofunction:: mirrorworld.streetview.find_panorama_async
    
    Usage sample::
    
      from mirrorworld import streetview
      from aiohttp import ClientSession
      
      async with ClientSession() as session:
          pano = await streetview.find_panorama_async(45.59395, 24.631609, session)
          print(pano.id)
          print(pano.lat, pano.lon)
          print(pano.date)
     
    .. autofunction:: mirrorworld.streetview.find_panorama_by_id

    Usage sample::
    
      from mirrorworld import streetview
      
      pano = await streetview.find_panorama_by_id("Py5vaKsLWJG16XyZosdYBQ")
      print(pano.id)
      print(pano.lat, pano.lon)
      print(pano.date)
    
    .. autofunction:: mirrorworld.streetview.find_panorama_by_id_async
    
    Usage sample::
    
      from mirrorworld import streetview
      from aiohttp import ClientSession
      
      async with ClientSession() as session:
          pano = await streetview.find_panorama_by_id_async("Py5vaKsLWJG16XyZosdYBQ", session)
          print(pano.id)
          print(pano.lat, pano.lon)
          print(pano.date)
    
    .. autofunction:: mirrorworld.streetview.get_coverage_tile
    .. autofunction:: mirrorworld.streetview.get_coverage_tile_async
    .. autofunction:: mirrorworld.streetview.get_coverage_tile_by_latlon
    .. autofunction:: mirrorworld.streetview.get_coverage_tile_by_latlon_async

Downloading panoramas
---------------------
    .. autofunction:: mirrorworld.streetview.get_panorama
    .. autofunction:: mirrorworld.streetview.get_panorama_async
    .. autofunction:: mirrorworld.streetview.download_panorama
    
    Usage sample: ::
    
      from mirrorworld import streetview

      pano = streetview.find_panorama(46.883958, 12.169002)
      streetview.download_panorama(pano, f"{pano.id}.jpg")
      
    .. autofunction:: mirrorworld.streetview.download_panorama_async
    
    Usage sample::
    
      from mirrorworld import streetview
      from aiohttp import ClientSession
      
      async with ClientSession() as session:
          pano = await streetview.find_panorama_async(46.883958, 12.169002, session)
          await streetview.download_panorama_async(pano, f"{pano.id}.jpg", session)

Data classes
------------
    .. autoclass:: mirrorworld.streetview.panorama.Artwork
       :members:
    .. autoclass:: mirrorworld.streetview.panorama.ArtworkLink
       :members:
    .. autoclass:: mirrorworld.streetview.panorama.BusinessStatus
       :members:
       :member-order: bysource
    .. autoclass:: mirrorworld.streetview.panorama.BuildingLevel
       :members:
    .. autoclass:: mirrorworld.streetview.panorama.CaptureDate
       :members:
       :member-order: bysource
    .. autoclass:: mirrorworld.streetview.panorama.DepthMap
       :members:
    .. autoclass:: mirrorworld.streetview.panorama.LocalizedString
       :members:
    .. autoclass:: mirrorworld.streetview.panorama.Place
       :members:
    .. autoclass:: mirrorworld.streetview.panorama.StreetLabel
       :members:
    .. autoclass:: mirrorworld.streetview.panorama.StreetViewPanorama
       :members:
    .. autoclass:: mirrorworld.streetview.panorama.UploadDate
       :members:
       :member-order: bysource

Miscellaneous
-------------
    .. autofunction:: mirrorworld.streetview.build_permalink
    .. autofunction:: mirrorworld.streetview.util.is_third_party_panoid
