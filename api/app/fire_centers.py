import app.db.database


async def fetch():
    session = app.db.database.get_read_session()
    # pylint: disable=no-member
    # NOTE: simplify with a factor of 0.005 results in about 173kb of data, and seems to give
    # a fairly nice resolution.
    response = session.execute("""SELECT json_build_object(
        'type', 'FeatureCollection',
        'features', json_agg(ST_AsGeoJSON(t.*)::json)
    )
        FROM (
        SELECT ST_Simplify(geom, 0.005), name FROM fire_centers
    ) as t(geom, name)""")
    row = next(response)
    return row[0]
