""" Fetch c-haines geojson
"""
import logging
import app.db.database


logger = logging.getLogger(__name__)


async def fetch():
    """ Fetch polygon geojson
    """
    session = app.db.database.get_read_session()
    query = """select json_build_object(
        'type', 'FeatureCollection',
        'features', json_agg(ST_AsGeoJSON(t.*)::json)
    )
        from (
        select geom, severity from prediction_model_c_haines_polygons
    ) as t(geom, severity) """
    # something is wrong here.
    logger.info('fetching geojson from db...')
    # pylint: disable=no-member
    response = session.execute(query)
    row = next(response)
    logger.info('returning response...')
    return row[0]
