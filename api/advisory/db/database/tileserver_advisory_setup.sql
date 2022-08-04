CREATE TABLE IF NOT EXISTS advisory_fire_zones (
    id SERIAL PRIMARY KEY,
    for_date DATE NOT NULL,
    mof_fire_zone_id integer NOT NULL,
    elevated_hfi_area double precision NOT NULL,
    elevated_hfi_percentage double precision NOT NULL
);
COMMENT ON TABLE advisory_fire_zones IS 'Information about advisories.';
CREATE INDEX IF NOT EXISTS ix_advisory_fire_zones_id ON advisory_fire_zones(id int4_ops);
CREATE INDEX IF NOT EXISTS ix_advisory_fire_zones_mof_fire_zone_id ON advisory_fire_zones(mof_fire_zone_id int4_ops);
CREATE INDEX IF NOT EXISTS ix_advisory_date ON advisory_fire_zones ((for_date::date));

ALTER USER tileserv WITH SUPERUSER;
grant connect on database tileserv to tileserv; grant usage on schema public to tileserv; grant select on all tables in schema public to tileserv;