""" Geospatial things
"""
from typing import Final
from pyproj import CRS

# Some constants that are frequently used when transforming coordinates.

# BCGOV standard is to store everything in NAD83 / BC Albers (EPSG:3005).
NAD83_BC_ALBERS: Final = 3005
# NAD 83 alone (EPSG:4269), uses geographic coordinates.
NAD83: Final = 'epsg:4269'
NAD83_CRS: Final = CRS(NAD83)
# De facto standard is to expose data in WGS84 (EPSG:4326).
WGS84: Final = 'epsg:4326'
