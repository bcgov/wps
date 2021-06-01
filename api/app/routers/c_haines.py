""" Routes for c-haines
"""
from enum import Enum
from datetime import datetime
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse, Response
from app.weather_models import ModelEnum
from app.c_haines.fetch import (fetch_prediction_geojson,
                                fetch_model_runs,
                                fetch_model_run_kml_streamer,
                                fetch_prediction_kml_streamer,
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


@router.get('/{model}/predictions')
async def get_c_haines_model_run(
        model: ModelEnum,
        model_run_timestamp: datetime = None,
        response_format: FormatEnum = FormatEnum.GEOJSON):
    """ Return geojson/kml polygons for c-haines """
    logger.info('/c-haines/%s/predictions?model_run_timestamp=%s&response_format=%s',
                model, model_run_timestamp, response_format)
    if response_format == FormatEnum.GEOJSON:
        raise HTTPException(status_code=501)
    # Let the browser cache the data as much as it wants.
    headers = {"Cache-Control": "max-age=3600, public, immutable"}
    headers["Content-Type"] = kml_media_type
    if model_run_timestamp is None:
        filename = f'{model}.kml'
    else:
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
    # Let the browser cache the data as much as it wants.
    headers = {"Cache-Control": "max-age=3600, public, immutable"}

    if response_format == FormatEnum.GEOJSON:
        geojson_response = await fetch_prediction_geojson(
            model, model_run_timestamp, prediction_timestamp)
        # We check for features - if there are no features, we return a 404.
        # NOTE: Technically, we should only return 404 if we're certain there is no record in the database...
        if geojson_response['features']:
            return JSONResponse(
                content=geojson_response,
                headers=headers)
        raise HTTPException(status_code=404)

    headers["Content-Type"] = kml_media_type
    headers["Content-Disposition"] = "inline;filename={}-{}-{}.kml".format(
        model, model_run_timestamp, prediction_timestamp)
    return StreamingResponse(fetch_prediction_kml_streamer(
        model, model_run_timestamp, prediction_timestamp),
        headers=headers, media_type=kml_media_type)


@router.get('/model-runs')
async def get_model_runs(model_run_timestamp: datetime = None):
    """ Return a list of recent model runs """
    logger.info('/c-haines/model-runs')
    return await fetch_model_runs(model_run_timestamp)


@router.get('/network-link')
async def get_kml_network_link():
    """ Return KML network link file """
    headers = {"Content-Type": kml_media_type,
               "Content-Disposition": "inline;filename=c-haines-network-link.kml"}

    return Response(headers=headers, media_type=kml_media_type, content=fetch_network_link_kml())
