# Simplify

If we have WGS84 (EPSG:4326), and we want to convert to NAD83 / BC Albers (EPSG:3005)


1. transform from 4326 to 3005
2. simplify to 2000
3. transform from 3005 to 4326

update all the zones in place, to have a lower resolution
```sql
update zones_wgs84 set wkb_geometry = ST_Transform(ST_Simplify(ST_Transform(zones_wgs84.wkb_geometry, 3005), 2000), 4326);

update zones_wgs84 set wkb_geometry = ST_Transform(ST_Simplify(ST_Transform(zones_wgs84.wkb_geometry, 3005), 32), 4326);


update fire_centres set geom = ST_Transform(ST_Simplify(ST_Transform(geom, 3005), 128, true), 4326);
```
at 128, borders start not matching up nicely!
at 64, borders start not matching up nicely!
at 32, things are getting blocky, but still pretty decent! there some borders not matching up.
at 16, things are getting blocky, but still pretty decent! there some borders not matching up.
at 8, you have to zoom in pretty far to start getting artifacts
at 4, you have to zoom in pretty far to start getting artifacts
at 2, you have artifacts - but looks pretty good to me!


```sql
select ST_Transform(ST_Simplify(ST_Transform(zones_wgs84.wkb_geometry, 3005), 2000), 4326) * from zones_wgs84 where ogc_fid = 1;
```