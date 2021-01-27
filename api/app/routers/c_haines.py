""" Routes for c-haines
"""
from datetime import datetime
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.weather_models import ModelEnum
from app.c_haines import fetch

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/c-haines",
)


@router.get('/{model}/')
async def get_c_haines(
        model: ModelEnum,
        model_run_timestamp: datetime,
        prediction_timestamp: datetime):
    """ Return geojson polygons for c-haines """
    logger.info('/c-haines/%s/?model_run_timestamp=%s&prediction_timestamp=%s',
                model, model_run_timestamp, prediction_timestamp)
    # Let the browser cache the data as much as it wants.
    headers = {"Cache-Control": "max-age=604800, public, immutable"}
    geojson_response = await fetch.fetch_prediction(model, model_run_timestamp, prediction_timestamp)
    # We check for features - if there are no features, we return a 404.
    # NOTE: Technically, we should only return 404 if we're certain there is no record in the database...
    if geojson_response['features']:
        return JSONResponse(
            content=geojson_response,
            headers=headers)
    raise HTTPException(status_code=404)


@router.get('/model-runs')
async def get_model_runs(model_run_timestamp: datetime = None):
    """ Return a list of recent model runs """
    logger.info('/c-haines/model-runs')
    # if model_run_timestamp:
    # model_run_timestamp.replace()
    return await fetch.fetch_model_runs(model_run_timestamp)
