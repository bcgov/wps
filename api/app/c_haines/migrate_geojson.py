"""
Code to migrate geometries from database to object storage.

NOTE: Once migration is complete - this script can be safely deleted.

This code can be run against the live database, or agains a copy of the live database.
run:
poetry shell
python -m app.c_haines.migrate_geojson
"""
import logging
import io
import json
from sqlalchemy import desc
from app import configure_logging
from app.utils.s3 import get_minio_client, object_exists
import app.db.database
from app.db.crud.c_haines import get_prediction_geojson
from app.db.models.weather_models import PredictionModel
from app.db.models.c_haines import CHainesPrediction, CHainesModelRun
from app.weather_models import ModelEnum
from app.c_haines.object_store import ObjectTypeEnum, generate_full_object_store_path

logger = logging.getLogger(__name__)


def main():
    """ entry point for migration """
    # create the client for our object store.
    client, bucket = get_minio_client()
    # open db connection.
    with app.db.database.get_read_session_scope() as session:
        # iterate through all c_haines model run predictions ever.
        query = session.query(CHainesModelRun, PredictionModel, CHainesPrediction)\
            .join(PredictionModel, CHainesModelRun.prediction_model_id == PredictionModel.id)\
            .join(CHainesPrediction, CHainesModelRun.id == CHainesPrediction.model_run_id)\
            .order_by(desc(CHainesModelRun.model_run_timestamp))
        for model_run, model, prediction in query:
            # log some output.
            logger.info('processing %s; model run: %s; prediction: %s', model.abbreviation,
                        model_run.model_run_timestamp, prediction.prediction_timestamp)

            prediction_model = ModelEnum(model.abbreviation)

            # create path that this is going to live on on the object store.
            target_geojson_path = generate_full_object_store_path(prediction_model,
                                                                  model_run.model_run_timestamp,
                                                                  prediction.prediction_timestamp,
                                                                  ObjectTypeEnum.GEOJSON)

            # let's save some time, and check if the file doesn't already exists.
            # it's duper important we do this, since this is a mega migration and we expect to restart
            # it a few times before it's all done.
            if object_exists(client, bucket, target_geojson_path):
                logger.info('json (%s) already exists, skipping', target_geojson_path)
                continue

            # fetch geojson for this prediction.
            geojson = get_prediction_geojson(session, prediction_model,
                                             model_run.model_run_timestamp,
                                             prediction.prediction_timestamp)

            # awesome - this is the exact geojson we want to upload
            with io.StringIO() as sio:
                json.dump(geojson, sio)
                # smash it into binary
                sio.seek(0)
                bio = io.BytesIO(sio.read().encode('utf8'))
                # get file size.
                size = bio.seek(0, io.SEEK_END)
                # go back to start
                bio.seek(0)
                # smash it into the object store.
                logger.info('uploading %s (%s)', target_geojson_path, size)
                client.put_object(bucket, target_geojson_path, bio, size)


if __name__ == '__main__':
    configure_logging()
    main()
