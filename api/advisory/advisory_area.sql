-- get the combustable area of fire zones
select 
	advisory_shapes.source_identifier,
 	advisory_shapes.id,
	ST_Area(advisory_shapes.geom) as zone_area,
	ST_Area(ST_Intersection(ST_Union(advisory_fuel_types.geom), advisory_shapes.geom)) as fuel_types,
	ST_Area(ST_Intersection(ST_Union(advisory_fuel_types.geom), advisory_shapes.geom))/ST_Area(advisory_shapes.geom)
from advisory_shapes
JOIN advisory_fuel_types ON ST_Intersects(advisory_fuel_types.geom, advisory_shapes.geom)
where fuel_type_id not in (-10000, 99, 102)
group by advisory_shapes.id
order by source_identifier;



-- select * from advisory_fuel_types limit 1;

-- get the area of fire zones

select ST_Area(geom) area_wgs84, -- ST_Area in wgs84 doesn't give you square meters!
	   ST_Area(ST_Transform(geom, 3005)) area_nad83_bc_albers, -- We need to convert to NAD83 / BC Albers to get meters
	   ST_GeometryType(geom), -- we're expecting multipolygons
	   ST_SRID(geom), -- in the database, we're storing it as WGS84 (4326), for serving up webmap faster
	   mof_fire_zone_name -- nice to know what we're looking at
	   from fire_zones


-- area of polygons that intersect with fire zones - but that's not the whole story!
-- we only want to calculate the area of actual intersection!
SELECT fire_zones.id, mof_fire_zone_name,
ST_Area(ST_Transform(geom, 3005)) zone_area,
SUM(ST_Area(ST_Transform(hfi.wkb_geometry, 3005))) hfi_area,
SUM(ST_Area(ST_Transform(hfi.wkb_geometry, 3005)))/ST_Area(ST_Transform(geom, 3005))*100 as percentage
FROM fire_zones
JOIN hfi ON ST_Intersects(fire_zones.geom, hfi.wkb_geometry)
GROUP BY fire_zones.id
ORDER by percentage desc


-- this is the whole story - the area in a fire zone that has high hfi
-- this query is hella slow!
SELECT fire_zones.id, mof_fire_zone_name,
-- make it NAD83 / BC Albers, then calculate the area
ST_Area(ST_Transform(fire_zones.geom, 3005)) zone_area,
-- we make a big fat union of all the hfi geometries (ST_Union) that intersect with the fire zones (JOIN with ST_Intersects)
-- then we crop it per fire zone (ST_Intersection)
-- then we make it NAD83 / BC Albers
-- then we calculate the area
ST_Area(ST_Transform( ST_Intersection(ST_Union(hfi.wkb_geometry), fire_zones.geom) , 3005)) hfi_area,
-- percentage of zone with high hfi
ST_Area(ST_Transform( ST_Intersection(ST_Union(hfi.wkb_geometry), fire_zones.geom) , 3005))/ST_Area(ST_Transform(fire_zones.geom, 3005))*100 percentage
FROM fire_zones
JOIN hfi ON ST_Intersects(fire_zones.geom, hfi.wkb_geometry)
GROUP BY fire_zones.id
ORDER BY percentage desc



SELECT fire_centres.id, mof_fire_centre_name,
-- make it NAD83 / BC Albers, then calculate the area
ST_Area(ST_Transform(fire_centres.geom, 3005)) centre_area,
-- we make a big fat union of all the hfi geometries (ST_Union)
-- then we crop it per fire centre (ST_Intersection)
-- then we make it NAD83 / BC Albers
-- then we calculate the area
ST_Area(ST_Transform( ST_Intersection(ST_Union(hfi.wkb_geometry), fire_centres.geom) , 3005)) hfi_area,
-- percentage of zone with high hfi
ST_Area(ST_Transform( ST_Intersection(ST_Union(hfi.wkb_geometry), fire_centres.geom) , 3005))/ST_Area(ST_Transform(fire_centres.geom, 3005))*100 percentage
FROM fire_centres
JOIN hfi ON ST_Intersects(fire_centres.geom, hfi.wkb_geometry)
GROUP BY fire_centres.id
ORDER BY percentage desc