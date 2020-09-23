""" Split geography of BC into a grid system, where each square of grid is 1 km x 1 km.
Code adapted from
https://stackoverflow.com/questions/40342355/how-can-i-generate-a-regular-geographic-grid-using-python
"""

import numpy as np
import shapely.geometry
import pyproj

# Set up coordinate transformer - transform lat/long (EPSG 4326) to BC Albers (EPSG 3005)
transformer = pyproj.Transformer.from_crs(4326, 3005)

# Create the southwest and northeast corners of BC's border
# southwest = shapely.geometry.Point(48.919726, -125.498744)  # Ucluelet
# northeast = shapely.geometry.Point(51.916258, -117.129908)  # Shuswap/Jasper National Park
# southwest = shapely.geometry.Point(50.3217, -121.2827)
# northeast = shapely.geometry.Point(51.0387, -119.5579)
# southwest = shapely.geometry.Point(49.1412, -125.5179)  # Alberni
# northeast = shapely.geometry.Point(52.000, -117.3222)  # Shuswap
# southwest = shapely.geometry.Point(49.4254, -119.7431)  # Penticton
# northeast = shapely.geometry.Point(49.6331, -119.3998)  # Penticton
southwest = shapely.geometry.Point(47.3638, -138.6576)  # all BC
northeast = shapely.geometry.Point(60.2145, -114.9271)  # all BC

stepsize = 1000  # 1 km grid step size

# Transform corner coordinates from lat/long to BC Albers
albers_southwest = transformer.transform(southwest.x, southwest.y)
albers_northeast = transformer.transform(northeast.x, northeast.y)
print(albers_southwest)
print(albers_northeast)

# Iterate over 2D area
# gridpoints = [[]]
# counter = 0
# x = albers_southwest[0]
# while x < albers_northeast[0]:
#     y = albers_southwest[1]
#     while y < albers_northeast[1]:
#         print(x, y)
#         p = transformer.transform(x, y)
#         # print(p)
#         gridpoints[counter].append(p)
#         y += stepsize
#     x += stepsize
#     counter += 1
#     gridpoints.append([])
# NOTE: gridpoints is 572 x 372 array
