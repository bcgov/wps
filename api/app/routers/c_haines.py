""" Routes for c-haines
"""
from datetime import datetime
from enum import Enum
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from app.weather_models import ModelEnum
from app.c_haines import fetch

logger = logging.getLogger(__name__)


class FormatEnum(str, Enum):
    """ Enumerator for different kinds of supported weather models """
    geoJSON = 'geoJSON'
    KML = 'KML'


router = APIRouter(
    prefix="/c-haines",
)


@router.get('/{model}/predictions')
async def get_c_haines_model_run(
        model: ModelEnum,
        model_run_timestamp: datetime,
        response_format: FormatEnum = FormatEnum.geoJSON):
    """ Return geojson polygons for c-haines """
    logger.info('/c-haines/%s/predictions?model_run_timestamp=%s&response_format=%s',
                model, model_run_timestamp, response_format)
    # Let the browser cache the data as much as it wants.
    headers = {"Cache-Control": "max-age=604800, public, immutable"}

    if response_format == FormatEnum.geoJSON:
        raise HTTPException(status_code=501)

    headers["Content-Type"] = "application/vnd.google-earth.kml+xml"
    headers["Content-Disposition"] = "inline;filename={}-{}.kml".format(
        model, model_run_timestamp)
    return StreamingResponse(
        fetch.fetch_model_run_kml_streamer(model, model_run_timestamp),
        headers=headers)


@router.get('/{model}/prediction')
async def get_c_haines_model_run_prediction(
        model: ModelEnum,
        model_run_timestamp: datetime,
        prediction_timestamp: datetime,
        response_format: FormatEnum = FormatEnum.geoJSON):
    """ Return geojson polygons for c-haines """
    logger.info('/c-haines/%s/prediction?model_run_timestamp=%s&prediction_timestamp=%s&response_format=%s',
                model, model_run_timestamp, prediction_timestamp, response_format)
    # Let the browser cache the data as much as it wants.
    headers = {"Cache-Control": "max-age=604800, public, immutable"}

    if response_format == FormatEnum.geoJSON:
        geojson_response = await fetch.fetch_prediction_geojson(model, model_run_timestamp, prediction_timestamp)
        # We check for features - if there are no features, we return a 404.
        # NOTE: Technically, we should only return 404 if we're certain there is no record in the database...
        if geojson_response['features']:
            return JSONResponse(
                content=geojson_response,
                headers=headers)
        raise HTTPException(status_code=404)

    headers["Content-Type"] = "application/vnd.google-earth.kml+xml"
    headers["Content-Disposition"] = "inline;filename={}-{}-{}.kml".format(
        model, model_run_timestamp, prediction_timestamp)
    return StreamingResponse(
        fetch.fetch_prediction_kml_streamer(
            model, model_run_timestamp, prediction_timestamp),
        headers=headers)


@router.get('/model-runs')
async def get_model_runs(model_run_timestamp: datetime = None):
    """ Return a list of recent model runs """
    logger.info('/c-haines/model-runs')
    # if model_run_timestamp:
    # model_run_timestamp.replace()
    return await fetch.fetch_model_runs(model_run_timestamp)
