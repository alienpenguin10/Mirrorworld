# Mirrorworld addition (not in upstream streetlevel).
"""
LiDAR point clouds for a bounding box. :mod:`mirrorworld.lidar.ept` reads any Entwine Point Tile (EPT) dataset
over HTTP, fetching only the octree nodes that intersect the box down to a chosen point spacing;
:mod:`mirrorworld.lidar.usgs3dep` finds and reads the USGS 3DEP collection (US-wide, public domain, on AWS);
:mod:`mirrorworld.lidar.ea` downloads and crops Environment Agency National LIDAR Programme tiles (England, OGL v3).
Results are ``laspy.LasData`` objects, ready to filter, convert or write as LAS/LAZ. Needs
``pip install mirrorworld[lidar]`` (laspy with LAZ support).
"""
