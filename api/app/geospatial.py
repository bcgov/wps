""" Geospatial things
"""
from typing import Final
from pyproj import CRS

# Some constants that are frequently used when transforming coordinates.

# BCGOV standard is to store everything in NAD83 (EPSG:4269).
NAD83: Final = 'epsg:4269'
NAD83_CRS: Final = CRS(NAD83)
# De facto standard is to expose data in WGS84 (EPSG:4326).
WGS84_EPSG: Final = 4326
WGS84: Final = 'epsg:4326'
