"""
Code to migrate geometries from database to object storage.

NOTE: Once migration is complete - this script can be safely deleted.

This code can be run against the live database, or agains a copy of the live database.
run:
poetry shell
python -m app.c_haines.migrate
"""
import logging
import tempfile
import os
from sqlalchemy import asc
from pyproj import Transformer, Proj
from app import configure_logging
from app.utils.minio import get_minio_client, object_exists
import app.db.database
from app.geospatial import NAD83, WGS84
from app.db.crud.c_haines import get_prediction_geojson
from app.db.models.weather_models import PredictionModel
from app.db.models.c_haines import CHainesPrediction, CHainesModelRun
from app.weather_models import ModelEnum
from app.c_haines.kml import generate_kml_prediction, feature_2_kml_polygon
from app.c_haines.severity_index import generate_full_kml_path

logger = logging.getLogger(__name__)


class KMLGeojsonPolygonIterator:
    """ Generator that produces a kml polygon for every geojson feature. This generator assumes GeoJSON
    as provided by DB query. """

    def __init__(self, geojson):
        self.features = iter(geojson['features'])
        # Source coordinate system is NAD83 as stored in the databse.
        proj_from = Proj(NAD83)
        # Destination coordinate systems is WGS84 for google earth KML.
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
    # create the client for our object store.
    client, bucket = get_minio_client()
    # open db connection.
    with app.db.database.get_read_session_scope() as session:
        # iterate through all c_haines model run predictions ever.
        query = session.query(CHainesModelRun, PredictionModel, CHainesPrediction)\
            .join(PredictionModel, CHainesModelRun.prediction_model_id == PredictionModel.id)\
            .join(CHainesPrediction, CHainesModelRun.id == CHainesPrediction.model_run_id)\
            .order_by(asc(CHainesModelRun.model_run_timestamp))
        for model_run, model, prediction in query:
            # log some output.
            logger.info('processing %s; model run: %s; prediction: %s', model.abbreviation,
                        model_run.model_run_timestamp, prediction.prediction_timestamp)

            prediction_model = ModelEnum(model.abbreviation)

            # create path that this is going to live on on the object store.
            target_kml_path = generate_full_kml_path(prediction_model,
                                                     model_run.model_run_timestamp,
                                                     prediction.prediction_timestamp)

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

            # generate the kml file.
            # we're going to put it in a temporary folder.
            with tempfile.TemporaryDirectory() as temporary_path:
                # construct an iterator that will eat geojson features and produce kml polygons.
                polygon_iterator = KMLGeojsonPolygonIterator(geojson)
                # we store the kml file temporarily.
                tmp_filename = os.path.join(temporary_path, 'kml.kml')
                with open(tmp_filename, 'w') as kml_file:
                    # iterate through the parts of the kml generator, writing each part to file
                    for polygon in generate_kml_prediction(polygon_iterator,
                                                           model,
                                                           model_run.model_run_timestamp,
                                                           prediction.prediction_timestamp):
                        kml_file.write(polygon)
                    # flush to disk
                    kml_file.flush()
                # smash it into the object store.
                client.fput_object(bucket, target_kml_path, tmp_filename)


if __name__ == '__main__':
    configure_logging()
    main()
