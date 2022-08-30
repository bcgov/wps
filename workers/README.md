# Simplify

If we have WGS84 (EPSG:4326), and we want to convert to NAD83 / BC Albers (EPSG:3005)


1. transform from 4326 to 3005
2. simplify to 2000
3. transform from 3005 to 4326

update all the zones in place, to have a lower resolution
```sql
update zones_wgs84 set wkb_geometry = ST_Transform(ST_Simplify(ST_Transform(zones_wgs84.wkb_geometry, 3005), 2000), 4326)
```

```sql
select ST_Transform(ST_Simplify(ST_Transform(zones_wgs84.wkb_geometry, 3005), 2000), 4326) * from zones_wgs84 where ogc_fid = 1;
```