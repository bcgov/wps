""" Fetch c-haines geojson
"""
from datetime import datetime
import logging
import app.db.database


logger = logging.getLogger(__name__)


async def fetch(model_run_timestamp: datetime, prediction_timestamp: datetime):
    """ Fetch polygon geojson
    """
    # TODO: Add filters for model and timestamp (returning only the most recent model run)
    session = app.db.database.get_read_session()
    # Ordering by severity, ascending is important to ensure that
    # higher severity is placed over lower severity. (On the front end,
    # it makes it easier to have the high severity border sit on top and
    # pop nicely.)
    query = """select json_build_object(
        'type', 'FeatureCollection',
        'features', json_agg(ST_AsGeoJSON(t.*)::json)
    )
        from (
        select geom, severity from prediction_model_c_haines_polygons
        where 
            prediction_timestamp = '2021-01-15 04:00:00-08' and
            model_run_timestamp = '2021-01-15 04:00:00-08'
        order by severity asc
    ) as t(geom, severity)"""
    # something is wrong here.
    logger.info('fetching geojson from db...')
    # pylint: disable=no-member
    response = session.execute(query)
    row = next(response)
    logger.info('returning response...')
    return row[0]
