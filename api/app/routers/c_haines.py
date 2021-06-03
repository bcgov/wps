""" Routes for c-haines
"""
from enum import Enum
from functools import reduce
from datetime import datetime
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse, Response
from starlette.responses import RedirectResponse
from app.minio_utils import get_minio_client
from app.weather_models import ModelEnum
from app.c_haines.severity_index import generate_full_kml_path
from app.c_haines.fetch import (fetch_prediction_geojson,
                                fetch_model_runs,
                                fetch_model_run_kml_streamer,
                                fetch_network_link_kml)


logger = logging.getLogger(__name__)


kml_media_type = 'application/vnd.google-earth.kml+xml'


class FormatEnum(str, Enum):
    """ Enumerator for different kinds of supported weather models """
    GEOJSON = 'geoJSON'
    KML = 'KML'


router = APIRouter(
    prefix="/c-haines",
)


class NoModelRunFound(Exception):
    """ Exception thrown when no model run can be found """


def _get_most_recent_kml_model_run(model: ModelEnum) -> datetime:
    """ Get the most recent model run date - if none exists, return None """
    # NOTE: This is a nasty, slow, brute force way of doing it!
    client, bucket = get_minio_client()

    def get_most_recent(result, depth):
        # use a reducer to iterate through the list of objects, returning the last one.
        last_object = reduce(lambda _, y: y, result)
        if last_object is None:
            return None
        if depth == 3:
            return last_object
        return get_most_recent(client.list_objects(bucket, last_object.object_name), depth+1)

    most_recent = get_most_recent(client.list_objects(bucket, f'c-haines-polygons/kml/{model}/'), 0)

    if most_recent is None:
        raise NoModelRunFound(f'no model run found for {model}')

    logger.info('most record model run: %s', most_recent.object_name)

    name_split = most_recent.object_name.strip('/').split('/')
    hour = int(name_split[-1])
    day = int(name_split[-2])
    month = int(name_split[-3])
    year = int(name_split[-4])
    return datetime(year=year, month=month, day=day, hour=hour, tzinfo=timezone.utc)


@router.get('/{model}/predictions')
async def get_c_haines_model_run(
        model: ModelEnum,
        model_run_timestamp: datetime = None,
        response_format: FormatEnum = FormatEnum.GEOJSON):
    """ Return geojson/kml polygons for c-haines """
    logger.info('/c-haines/%s/predictions?model_run_timestamp=%s&response_format=%s',
                model, model_run_timestamp, response_format)
    if response_format == FormatEnum.GEOJSON:
        # Not implemented for GeoJSON
        raise HTTPException(status_code=501)
    headers = {"Content-Type": kml_media_type}
    if model_run_timestamp is None:
        model_run_timestamp = _get_most_recent_kml_model_run(model)
    if model_run_timestamp is None:
        # most recent model not found
        raise HTTPException(status_code=404)
    filename = f'{model}-{model_run_timestamp}.kml'
    headers["Content-Disposition"] = "inline;filename={}".format(
        filename)
    response = StreamingResponse(
        fetch_model_run_kml_streamer(model, model_run_timestamp),
        headers=headers,
        media_type=kml_media_type)
    return response


@router.get('/{model}/prediction')
async def get_c_haines_model_run_prediction(
        model: ModelEnum,
        model_run_timestamp: datetime,
        prediction_timestamp: datetime,
        response_format: FormatEnum = FormatEnum.GEOJSON):
    """ Return geojson/kml polygons for c-haines """
    logger.info('/c-haines/%s/prediction?model_run_timestamp=%s&prediction_timestamp=%s&response_format=%s',
                model, model_run_timestamp, prediction_timestamp, response_format)

    if response_format == FormatEnum.GEOJSON:
        geojson_response = await fetch_prediction_geojson(
            model, model_run_timestamp, prediction_timestamp)
        # We check for features - if there are no features, we return a 404.
        # NOTE: Technically, we should only return 404 if we're certain there is no record in the database...
        if geojson_response['features']:
            # Let the browser cache the data as much as it wants.
            headers = {"Cache-Control": "max-age=3600, public, immutable"}
            return JSONResponse(
                content=geojson_response,
                headers=headers)
        raise HTTPException(status_code=404)

    # else KML:
    headers = {"Content-Type": kml_media_type}
    headers["Content-Disposition"] = "inline;filename={}-{}-{}.kml".format(
        model, model_run_timestamp, prediction_timestamp)

    client, bucket = get_minio_client()
    url = client.get_presigned_url("GET", bucket, generate_full_kml_path(
        model, model_run_timestamp, prediction_timestamp))
    return RedirectResponse(url=url)


@router.get('/model-runs')
async def get_model_runs(model_run_timestamp: datetime = None):
    """ Return a list of recent model runs """
    logger.info('/c-haines/model-runs')
    return await fetch_model_runs(model_run_timestamp)


@router.get('/network-link')
async def get_kml_network_link():
    """ Return KML network link file """
    logger.info('/c-haines/network-link')
    headers = {"Content-Type": kml_media_type,
               "Content-Disposition": "inline;filename=c-haines-network-link.kml"}

    return Response(headers=headers, media_type=kml_media_type, content=fetch_network_link_kml())
