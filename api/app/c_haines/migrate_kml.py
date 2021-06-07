"""
Code to migrate geometries from database to object storage.

NOTE: Once migration is complete - this script can be safely deleted.

This code can be run against the live database, or agains a copy of the live database.
run:
poetry shell
python -m app.c_haines.migrate_kml
"""
import logging
import io
from sqlalchemy import desc
from app import configure_logging
from app.utils.s3 import get_minio_client, object_exists
import app.db.database
from app.db.crud.c_haines import get_prediction_geojson
from app.db.models.weather_models import PredictionModel
from app.db.models.c_haines import CHainesPrediction, CHainesModelRun
from app.weather_models import ModelEnum
from app.c_haines.kml import generate_kml_prediction, feature_2_kml_polygon
from app.c_haines.object_store import ObjectTypeEnum, generate_full_object_store_path

logger = logging.getLogger(__name__)


class KMLGeojsonPolygonIterator:
    """ Generator that produces a kml polygon for every geojson feature. This generator assumes GeoJSON
    as provided by DB query. No projection transformation is required, as the geojson from the database
    is already in WGS84. """

    def __init__(self, geojson):
        self.features = iter(geojson['features'])

    def __iter__(self):
        return self

    def __next__(self):
        feature = next(self.features)
        severity = feature['properties']['c_haines_index']
        return feature_2_kml_polygon(feature, None), severity


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
            target_kml_path = generate_full_object_store_path(prediction_model,
                                                              model_run.model_run_timestamp,
                                                              prediction.prediction_timestamp,
                                                              ObjectTypeEnum.KML)

            # let's save some time, and check if the file doesn't already exists.
            # it's duper important we do this, since this is a mega migration and we expect to restart
            # it a few times before it's all done.
            if object_exists(client, bucket, target_kml_path):
                logger.info('kml (%s) already exists, skipping', target_kml_path)
                continue

            # fetch geojson for this prediction.
            geojson = get_prediction_geojson(session, prediction_model,
                                             model_run.model_run_timestamp,
                                             prediction.prediction_timestamp)

            # construct an iterator that will eat geojson features and produce kml polygons.
            polygon_iterator = KMLGeojsonPolygonIterator(geojson)
            # create in memory file object
            with io.StringIO() as kml_file:
                # iterate through the parts of the kml generator, writing each part to file.
                for part in generate_kml_prediction(polygon_iterator,
                                                    prediction_model,
                                                    model_run.model_run_timestamp,
                                                    prediction.prediction_timestamp):
                    kml_file.write(part)
                # smash it into binary
                kml_file.seek(0)
                bio = io.BytesIO(kml_file.read().encode('utf8'))
                # get file size.
                size = bio.seek(0, io.SEEK_END)
                # go back to start
                bio.seek(0)
                # smash it into the object store.
                logger.info('uploading %s (%s)', target_kml_path, size)
                client.put_object(bucket, target_kml_path, bio, size)


if __name__ == '__main__':
    configure_logging()
    main()
