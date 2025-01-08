import geopandas as gpd
import numpy as np
from shapely.affinity import translate
from shapely.geometry import LineString, MultiLineString, MultiPolygon, Polygon
from shapely.ops import unary_union


# Function to extend a hotspot in a given wind direction
def extend_hotspot(hotspot, wind_angle, distance):
    """
    Extends a given hotspot in the wind direction by a certain distance.
    """
    # Create a buffer around the hotspot to simulate fire growth
    buffer_distance = distance  # Control this value based on how much the fire grows
    extended_hotspot = hotspot.buffer(buffer_distance)

    # Convert the wind angle from geographic to Cartesian
    wind_angle = wind_angle + 180
    cartesian_angle = (90 - wind_angle) % 360  # Adjust for Cartesian coordinates

    # Convert the Cartesian angle to radians
    wind_angle_radians = np.radians(cartesian_angle)

    # Calculate dx and dy based on the adjusted wind angle
    dx = np.cos(wind_angle_radians) * distance
    dy = np.sin(wind_angle_radians) * distance

    extended_finger = translate(extended_hotspot, xoff=dx, yoff=dy)

    return extended_finger


# Function to grow fire perimeter based on wind direction and hotspots
def grow_fire_perimeter(fire_perimeter, hotspots, wind_angle, distance=500, crs=3005):
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
    extended_fingers_gdf = gpd.GeoDataFrame(geometry=extended_fingers, crs=f"EPSG:{crs}")

    dissolved_hot_spots = extended_fingers_gdf.union_all()
    union_gdf = gpd.GeoDataFrame(geometry=[dissolved_hot_spots], crs=extended_fingers_gdf.crs)
    union_gdf = union_gdf.explode().reset_index(drop=True)

    # Step 2: Generate convex hulls for each geometry in union_gdf
    convex_hulls = [geom.convex_hull for geom in union_gdf.geometry]

    # Step 3: Create a new GeoDataFrame with the convex hulls
    convex_hulls_gdf = gpd.GeoDataFrame(geometry=convex_hulls, crs=extended_fingers_gdf.crs)

    # Optional: Remove holes from each convex hull geometry
    convex_hulls_gdf["geometry"] = convex_hulls_gdf["geometry"].apply(remove_holes)
    # extended_fingers_gdf.to_file("/Users/breedwar/Downloads/hackathon/hot_spots_buffered.geojson", driver="GeoJSON")

    # Combine the extended fingers with the original fire perimeter
    combined_perimeter = gpd.overlay(fire_perimeter, convex_hulls_gdf, how="union")

    # Dissolve to combine all the geometries into one final fire perimeter
    final_fire_perimeter = combined_perimeter.union_all()

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
# fire_perimeter_gdf = gpd.read_file("/Users/breedwar/Downloads/hackathon/PROT_CURRENT_FIRE_POLYS_SP.geojson")
# fire_perimeter_gdf = fire_perimeter_gdf.to_crs(epsg=3005)
# hotspots_gdf = gpd.read_file("/Users/breedwar/Downloads/hackathon/FirespotArea_canada_c6.1_48.geojson")
# hotspots_gdf = hotspots_gdf.to_crs(epsg=3005)

# wind_direction = 270

# # Grow the fire perimeter based on hotspots and wind direction
# new_fire_perimeter = grow_fire_perimeter(fire_perimeter_gdf, hotspots_gdf, wind_direction, distance=500)

# # Save the new fire perimeter to a file
# new_fire_perimeter_gdf = gpd.GeoDataFrame(geometry=[new_fire_perimeter], crs="EPSG:3005").to_crs(epsg=4326)
# new_fire_perimeter_gdf.to_file("/Users/breedwar/Downloads/hackathon/new_fire_perimeter.geojson", driver="GeoJSON")


def get_hotspots_within_boundary_or_outside_fire(fire_perimeter_gdf, hotspots_gdf, buffer_distance):
    """
    Identify hotspots that are:
    1. Near the fire boundary and inside the fire perimeter.
    2. Not within the fire perimeter.

    Parameters:
    - fire_perimeter_gdf (GeoDataFrame): GeoDataFrame containing fire perimeter polygons.
    - hotspots_gdf (GeoDataFrame): GeoDataFrame containing hotspot points.
    - buffer_distance (float): Distance (in CRS units) to buffer around the hotspots.

    Returns:
    - GeoDataFrame: Filtered GeoDataFrame with hotspots that satisfy the specified conditions.
    """
    # Ensure CRS matches between fire perimeter and hotspots
    if fire_perimeter_gdf.crs != hotspots_gdf.crs:
        hotspots_gdf = hotspots_gdf.to_crs(fire_perimeter_gdf.crs)

    # Step 1: Get the fire perimeter boundaries and full fire perimeter
    fire_boundary = fire_perimeter_gdf.boundary.unary_union
    fire_perimeter = fire_perimeter_gdf.unary_union

    # Step 2: Buffer the hotspots
    hotspots_gdf["buffered_geometry"] = hotspots_gdf.geometry.buffer(buffer_distance)

    # Step 3: Determine if hotspots are near the boundary
    hotspots_gdf["near_boundary"] = hotspots_gdf["buffered_geometry"].intersects(fire_boundary)

    # Step 4: Determine if hotspots are within the fire perimeter
    hotspots_gdf["within_fire"] = hotspots_gdf.geometry.within(fire_perimeter)

    # Step 5: Select hotspots that are either:
    # 1. Near the fire boundary and within the fire perimeter, OR
    # 2. Not within the fire perimeter
    selected_hotspots = hotspots_gdf[(hotspots_gdf["near_boundary"] & hotspots_gdf["within_fire"]) | (~hotspots_gdf["within_fire"])].copy()

    # Drop the temporary buffered geometry column
    selected_hotspots.drop(columns=["buffered_geometry"], inplace=True)

    return selected_hotspots
