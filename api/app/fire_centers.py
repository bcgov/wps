import app.db.database


async def fetch():
    session = app.db.database.get_read_session()
    # pylint: disable=no-member
    # NOTE: simplify with a factor of 0.005 results in about 173kB of data, and seems to give
    # a fairly nice resolution.
    # simplify with 0.0005 results in about 1.2MB of data.
    response = session.execute("""SELECT json_build_object(
        'type', 'FeatureCollection',
        'features', json_agg(ST_AsGeoJSON(t.*)::json)
    )
        FROM (
        SELECT ST_Simplify(geom, 0.0005), name FROM fire_centers
    ) as t(geom, name)""")
    row = next(response)
    return row[0]
