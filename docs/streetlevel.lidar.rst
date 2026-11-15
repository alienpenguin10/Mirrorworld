streetlevel.lidar: LiDAR point clouds
=====================================

Point clouds for a bounding box from Entwine Point Tile (EPT) datasets, fetching only the octree nodes that
intersect the box down to a chosen spacing. Returns ``laspy.LasData``. Needs ``pip install streetlevel[lidar]``.

USGS 3DEP
---------
    .. autofunction:: streetlevel.lidar.usgs3dep.find_datasets
    .. autofunction:: streetlevel.lidar.usgs3dep.get_points
    .. autofunction:: streetlevel.lidar.usgs3dep.get_points_async
    .. autofunction:: streetlevel.lidar.usgs3dep.download_points
    .. autoclass:: streetlevel.lidar.usgs3dep.Dataset
      :members:

    Usage sample::

      from streetlevel.lidar import usgs3dep

      print(usgs3dep.find_datasets(47.6068, -122.3340, 47.6058, -122.3325))
      las = usgs3dep.download_points(47.6068, -122.3340, 47.6058, -122.3325, "seattle.laz", resolution=1.0)
      ground = las.points[las.classification == 2]


Any EPT dataset
---------------
    .. autofunction:: streetlevel.lidar.ept.get_info
    .. autofunction:: streetlevel.lidar.ept.get_info_async
    .. autofunction:: streetlevel.lidar.ept.get_points
    .. autofunction:: streetlevel.lidar.ept.get_points_async
    .. autofunction:: streetlevel.lidar.ept.download_points
    .. autoclass:: streetlevel.lidar.ept.EptInfo
      :members:
