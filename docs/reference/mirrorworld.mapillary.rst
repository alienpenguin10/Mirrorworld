mirrorworld.mapillary: Mapillary
================================

Mapillary has a documented public API and needs a free access token (``MLY|...`` from
https://www.mapillary.com/dashboard/developers): pass ``access_token=`` or set ``MAPILLARY_ACCESS_TOKEN``.
Imagery is CC BY-SA 4.0. Images can be 360° panoramas or ordinary photos (``is_pano``).

Finding images
--------------
    .. autofunction:: mirrorworld.mapillary.find_panoramas
    .. autofunction:: mirrorworld.mapillary.find_panoramas_async
    .. autofunction:: mirrorworld.mapillary.find_panorama_by_id
    .. autofunction:: mirrorworld.mapillary.find_panorama_by_id_async
    .. autofunction:: mirrorworld.mapillary.get_coverage_tile
    .. autofunction:: mirrorworld.mapillary.get_coverage_tile_async
    .. autofunction:: mirrorworld.mapillary.get_coverage_tile_by_latlon
    .. autofunction:: mirrorworld.mapillary.get_coverage_tile_by_latlon_async
    .. autofunction:: mirrorworld.mapillary.get_sequence
    .. autofunction:: mirrorworld.mapillary.get_sequence_async

    Usage sample::

      from mirrorworld import mapillary

      panos = mapillary.find_panoramas(47.6062, -122.3321, radius=50, panos_only=True)
      pano = mapillary.find_panorama_by_id(panos[0].id)
      print(pano.date, pano.camera_type, pano.permalink)
      mapillary.download_panorama(pano, f"{pano.id}.jpg", size="original")

    Async::

      from mirrorworld import mapillary
      from aiohttp import ClientSession

      async with ClientSession() as session:
          panos = await mapillary.find_panoramas_async(47.6062, -122.3321, session, radius=50)
          await mapillary.download_panorama_async(panos[0], f"{panos[0].id}.jpg", session, size="2048")


Downloading images
------------------
    .. autofunction:: mirrorworld.mapillary.get_panorama
    .. autofunction:: mirrorworld.mapillary.get_panorama_async
    .. autofunction:: mirrorworld.mapillary.download_panorama
    .. autofunction:: mirrorworld.mapillary.download_panorama_async

Map features, detections and point clouds
-----------------------------------------
Objects triangulated from many images (utility poles, manholes, junction boxes, street lights, hydrants,
traffic signs, ...), per-image semantic segmentations and structure-from-motion point clouds.

    .. autofunction:: mirrorworld.mapillary.find_map_features
    .. autofunction:: mirrorworld.mapillary.find_map_features_async
    .. autofunction:: mirrorworld.mapillary.find_map_feature_by_id
    .. autofunction:: mirrorworld.mapillary.find_map_feature_by_id_async
    .. autofunction:: mirrorworld.mapillary.get_map_features_tile
    .. autofunction:: mirrorworld.mapillary.get_map_features_tile_async
    .. autofunction:: mirrorworld.mapillary.get_detections
    .. autofunction:: mirrorworld.mapillary.get_detections_async
    .. autofunction:: mirrorworld.mapillary.get_point_cloud
    .. autofunction:: mirrorworld.mapillary.get_point_cloud_async

    Usage sample::

      from mirrorworld import mapillary

      poles = mapillary.find_map_features(47.68, -122.30, radius=150,
                                          values=["object--support--utility-pole", "object--junction-box"])
      pole = mapillary.find_map_feature_by_id(poles[0].id)       # adds the images it was seen in
      detections = mapillary.get_detections(pole.image_ids[0])   # polygons in 0..1 image coordinates
      cloud = mapillary.get_point_cloud(pole.image_ids[0])       # cloud.xyz, cloud.rgb, cloud.to_wgs84()

Data classes
------------
    .. autoclass:: mirrorworld.mapillary.panorama.MapillaryPanorama
      :members:
    .. autoclass:: mirrorworld.mapillary.features.MapFeature
      :members:
    .. autoclass:: mirrorworld.mapillary.features.Detection
      :members:
    .. autoclass:: mirrorworld.mapillary.features.PointCloud
      :members:

Miscellaneous
-------------
    .. autofunction:: mirrorworld.mapillary.build_permalink
    .. autofunction:: mirrorworld.mapillary.get_access_token
