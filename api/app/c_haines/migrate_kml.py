"""
Code to migrate geometries from database to object storage.

NOTE: Once migration is complete - this script can be safely deleted.

run:
poetry shell
python -m app.c_haines.migrate
"""
import logging
import tempfile
import os
from pyproj import Transformer, Proj
from app import configure_logging
from app.minio_utils import get_minio_client
import app.db.database
from app.weather_models.process_grib import NAD83, WGS84
from app.db.crud.c_haines import get_prediction_geojson
from app.db.models.weather_models import PredictionModel
from app.db.models.c_haines import CHainesPrediction, CHainesModelRun
from app.weather_models import ModelEnum
from app.c_haines.kml import kml_prediction, feature_2_kml_polygon
from app.c_haines.severity_index import is_existing, generate_full_kml_path

logger = logging.getLogger(__name__)


class CHainesIndexIterator:
    """ Iterator that matches the result the crud function get_prediction_kml would give you """

    def __init__(self, geojson):
        self.features = iter(geojson['features'])
        # Source coordinate system, must match source data.
        proj_from = Proj(NAD83)
        # Destination coordinate systems (NAD83, geographic coordinates)
        proj_to = Proj(WGS84)
        self.project = Transformer.from_proj(proj_from, proj_to, always_xy=True)

    def __iter__(self):
        return self

    def __next__(self):
        feature = next(self.features)
        severity = feature['properties']['c_haines_index']
        return feature_2_kml_polygon(feature, self.project), severity


def main():
    """ entry point for migration """
    client, bucket = get_minio_client()
    with app.db.database.get_read_session_scope() as session:
        # iterate through all c_haines model run predictions ever
        for model_run, model, prediction in session.query(CHainesModelRun, PredictionModel, CHainesPrediction)\
                .join(PredictionModel, CHainesModelRun.prediction_model_id == PredictionModel.id)\
                .join(CHainesPrediction, CHainesModelRun.id == CHainesPrediction.model_run_id):
            # some output
            logger.info('processing %s; model run: %s; prediction: %s', model.abbreviation,
                        model_run.model_run_timestamp, prediction.prediction_timestamp)

            prediction_model = ModelEnum(model.abbreviation)

            target_kml_path = generate_full_kml_path(
                prediction_model, model_run.model_run_timestamp, prediction.prediction_timestamp)

            # let's save some time, and check if the file doesn't already exists.
            # it's super important we do this, since there are many c-haines cronjobs running in dev, all
            # pointing to the same s3 bucket.
            if is_existing(client, bucket, target_kml_path):
                logger.info('kml (%s) already exists, skipping', target_kml_path)
                continue

            # fetch geojson for this prediction
            geojson = get_prediction_geojson(session, prediction_model,
                                             model_run.model_run_timestamp, prediction.prediction_timestamp)

            # generate it
            with tempfile.TemporaryDirectory() as temporary_path:
                kml_file_result = CHainesIndexIterator(geojson)
                tmp_filename = os.path.join(temporary_path, 'kml.kml')
                with open(tmp_filename, 'w') as kml_file:
                    for part in kml_prediction(kml_file_result, model, model_run.model_run_timestamp, prediction.prediction_timestamp):
                        kml_file.write(part)
                    kml_file.flush()
                client.fput_object(bucket, target_kml_path, tmp_filename)


if __name__ == '__main__':
    configure_logging()
    main()
