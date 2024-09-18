import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon, LineString, MultiLineString
from shapely.affinity import translate
import numpy as np


# Function to extend a hotspot in a given wind direction
def extend_hotspot(hotspot, wind_angle, distance):
    """
    Extends a given hotspot in the wind direction by a certain distance.
    """
    # Create a buffer around the hotspot to simulate fire growth
    buffer_distance = distance  # Control this value based on how much the fire grows
    extended_hotspot = hotspot.buffer(buffer_distance)

    # Translate the buffer in the wind direction to create a 'finger' shape
    wind_angle_radians = np.radians(wind_angle)
    dx = np.cos(wind_angle_radians) * distance
    dy = np.sin(wind_angle_radians) * distance

    extended_finger = translate(extended_hotspot, xoff=dx, yoff=dy)

    return extended_finger


# Function to grow fire perimeter based on wind direction and hotspots
def grow_fire_perimeter(fire_perimeter, hotspots, wind_angle, distance=500):
    """
    Grows the fire perimeter based on wind direction and hotspot positions.
    """
    extended_fingers = []

    # Loop through each hotspot and extend it
    for hotspot in hotspots.geometry:
        # Extend the hotspot in the wind direction
        extended_finger = extend_hotspot(hotspot, wind_angle, distance)
        extended_fingers.append(extended_finger)

    # Create a GeoDataFrame of the extended 'fingers'
    extended_fingers_gdf = gpd.GeoDataFrame(geometry=extended_fingers, crs="EPSG:3005")
    extended_fingers_gdf["geometry"] = extended_fingers_gdf["geometry"].apply(remove_holes)

    # Combine the extended fingers with the original fire perimeter
    combined_perimeter = gpd.overlay(fire_perimeter, extended_fingers_gdf, how="union")

    # Dissolve to combine all the geometries into one final fire perimeter
    final_fire_perimeter = combined_perimeter.unary_union

    return final_fire_perimeter


def extend_fire_perimeter(fire_perimeter, wind_angle, distance):
    # TODO Figure out how to extend the fire perimeter the same direction as the wind, so there is no gap
    # between the extended hot spots and the fire perimeter
    """
    Extend the fire perimeter in the direction of the wind without buffering in all directions.
    """
    # Convert the fire perimeter to a line (or MultiLineString) to extend it
    fire_lines = fire_perimeter.geometry.boundary

    # Create a list to store the extended lines
    extended_lines = []

    # Calculate the wind direction in radians
    wind_angle_radians = np.radians(wind_angle)
    dx = np.cos(wind_angle_radians) * distance
    dy = np.sin(wind_angle_radians) * distance

    for line in fire_lines:
        if isinstance(line, LineString):
            # Extend the line in the wind direction
            extended_line = translate(line, xoff=dx, yoff=dy)
            extended_lines.append(extended_line)
        elif isinstance(line, MultiLineString):
            # Extend each line in the MultiLineString
            for l in line:
                extended_line = translate(l, xoff=dx, yoff=dy)
                extended_lines.append(extended_line)

    # Create a new GeoDataFrame for the extended lines
    extended_lines_gdf = gpd.GeoDataFrame(geometry=extended_lines, crs=fire_perimeter.crs)

    # Convert extended lines back to polygons to form the extended fire perimeter
    extended_polygons = extended_lines_gdf.buffer(distance / 2)  # Small buffer to form a polygon

    # Combine the extended polygons with the original fire perimeter
    combined_perimeter = gpd.GeoDataFrame(geometry=list(extended_polygons) + list(fire_perimeter.geometry), crs=fire_perimeter.crs)
    final_fire_perimeter = combined_perimeter.unary_union

    return final_fire_perimeter


def remove_holes(polygon):
    if polygon.is_empty:
        return polygon

    if isinstance(polygon, Polygon):
        return Polygon(polygon.exterior)

    elif isinstance(polygon, MultiPolygon):
        # Remove holes for each polygon in the MultiPolygon
        return MultiPolygon([Polygon(p.exterior) for p in polygon.geoms])

    return polygon


# Load fire perimeter and hotspots from GeoJSON or shapefiles
fire_perimeter_gdf = gpd.read_file("/Users/breedwar/Downloads/hackathon/PROT_CURRENT_FIRE_POLYS_SP.geojson")
fire_perimeter_gdf = fire_perimeter_gdf.to_crs(epsg=3005)
hotspots_gdf = gpd.read_file("/Users/breedwar/Downloads/hackathon/FirespotArea_canada_c6.1_48.geojson")
hotspots_gdf = hotspots_gdf.to_crs(epsg=3005)

wind_direction = 180  ## this direction doesn't quite make sense. 180 seems to be wind blowing to the east

# Grow the fire perimeter based on hotspots and wind direction
new_fire_perimeter = grow_fire_perimeter(fire_perimeter_gdf, hotspots_gdf, wind_direction, distance=500)

# Save the new fire perimeter to a file
new_fire_perimeter_gdf = gpd.GeoDataFrame(geometry=[new_fire_perimeter], crs="EPSG:3005").to_crs(epsg=4326)
# new_fire_perimeter_gdf["geometry"] = new_fire_perimeter_gdf["geometry"].apply(remove_holes)
new_fire_perimeter_gdf.to_file("/Users/breedwar/Downloads/hackathon/new_fire_perimeter3.geojson", driver="GeoJSON")
