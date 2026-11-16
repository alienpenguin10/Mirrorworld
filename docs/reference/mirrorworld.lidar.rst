mirrorworld.lidar: LiDAR point clouds
=====================================

Point clouds for a bounding box from Entwine Point Tile (EPT) datasets, fetching only the octree nodes that
intersect the box down to a chosen spacing. Returns ``laspy.LasData``. Needs ``pip install mirrorworld[lidar]``.

USGS 3DEP
---------
    .. autofunction:: mirrorworld.lidar.usgs3dep.find_datasets
    .. autofunction:: mirrorworld.lidar.usgs3dep.get_points
    .. autofunction:: mirrorworld.lidar.usgs3dep.get_points_async
    .. autofunction:: mirrorworld.lidar.usgs3dep.download_points
    .. autoclass:: mirrorworld.lidar.usgs3dep.Dataset
      :members:

    Usage sample::

      from mirrorworld.lidar import usgs3dep

      print(usgs3dep.find_datasets(47.6068, -122.3340, 47.6058, -122.3325))
      las = usgs3dep.download_points(47.6068, -122.3340, 47.6058, -122.3325, "seattle.laz", resolution=1.0)
      ground = las.points[las.classification == 2]


Any EPT dataset
---------------
    .. autofunction:: mirrorworld.lidar.ept.get_info
    .. autofunction:: mirrorworld.lidar.ept.get_info_async
    .. autofunction:: mirrorworld.lidar.ept.get_points
    .. autofunction:: mirrorworld.lidar.ept.get_points_async
    .. autofunction:: mirrorworld.lidar.ept.download_points
    .. autoclass:: mirrorworld.lidar.ept.EptInfo
      :members:
