import logging
from datetime import timedelta
import numpy as np
import math
import matplotlib.pyplot as plt
import csv
from matplotlib.ticker import MultipleLocator
from sklearn.linear_model import LinearRegression
from scipy.interpolate import griddata, interp1d
from geoalchemy2.shape import to_shape
from sqlalchemy import extract
from app import configure_logging
from app.stations import get_stations_sync

from app.db.database import get_session
from app.db.models import (
    HourlyActual, NoonForecast, PredictionModelGridSubset, ModelRunGridSubsetPrediction, PredictionModelRunTimestamp)


configure_logging()


logger = logging.getLogger()


def get_actuals(session, station_code):
    return session.query(HourlyActual)\
        .filter(HourlyActual.station_code == station_code)\
        .filter(HourlyActual.temp_valid == True)\
        .order_by(HourlyActual.weather_date.asc())


def get_actual(session, station_code, weather_date):
    return session.query(HourlyActual)\
        .filter(HourlyActual.station_code == station_code)\
        .filter(HourlyActual.temp_valid == True)\
        .filter(HourlyActual.weather_date == weather_date).first()


def get_coordinate_grid(session, latitude, longitude):
    return session.query(PredictionModelGridSubset).\
        filter(PredictionModelGridSubset.geom.ST_Contains(
            'POINT({longitude} {latitude})'.format(longitude=longitude, latitude=latitude))).first()


def most_recent_model_run(session, grid, weather_date):
    return session.query(ModelRunGridSubsetPrediction, PredictionModelRunTimestamp)\
        .filter(PredictionModelRunTimestamp.id == ModelRunGridSubsetPrediction.prediction_model_run_timestamp_id)\
        .filter(ModelRunGridSubsetPrediction.prediction_model_grid_subset_id == grid.id)\
        .filter(ModelRunGridSubsetPrediction.prediction_timestamp == weather_date)\
        .order_by(PredictionModelRunTimestamp.prediction_run_timestamp.desc()).first()


def get_noon_forecasts(session, station_code, start_date):
    return session.query(NoonForecast)\
        .filter(NoonForecast.station_code == station_code)\
        .filter(NoonForecast.temp_valid == True)\
        .filter(NoonForecast.weather_date >= start_date)\
        .order_by(NoonForecast.weather_date, NoonForecast.created_at)


def extract_one_day_forecast(query):
    forecasts = {}
    for forecast in query:
        delta = forecast.weather_date - forecast.created_at
        # only consider forecasts that are less than 24 hours old
        if delta.days < 1:
            # make sure, to even then, only take the latest.
            forecasts[forecast.weather_date] = forecast
    return forecasts.values()


def get_noon_model_prediction(session, grid, weather_date, points, target_coordinate):
    """ get one day prediction """
    end_bound = weather_date - timedelta(days=1)
    start_bound = weather_date - timedelta(days=1, hours=12)

    a = weather_date.replace(hour=18)
    b = weather_date.replace(hour=21)

    query = session.query(ModelRunGridSubsetPrediction, PredictionModelRunTimestamp)\
        .filter(PredictionModelRunTimestamp.id == ModelRunGridSubsetPrediction.prediction_model_run_timestamp_id)\
        .filter(ModelRunGridSubsetPrediction.prediction_model_grid_subset_id == grid.id)\
        .filter(ModelRunGridSubsetPrediction.prediction_timestamp.in_((a, b)))\
        .filter(PredictionModelRunTimestamp.prediction_run_timestamp <= end_bound)\
        .filter(PredictionModelRunTimestamp.prediction_run_timestamp >= start_bound)\
        .order_by(ModelRunGridSubsetPrediction.prediction_timestamp)\
        .order_by(PredictionModelRunTimestamp.prediction_run_timestamp).all()

    if query:
        before = query[0][0]
        after = query[1][0]

        # x-axis is the timestamp
        x_axis = (before.prediction_timestamp.timestamp(), after.prediction_timestamp.timestamp())
        # y-axis is the temperature at 18 and the temperature at 21
        y_axis = [
            [before.tmp_tgl_2[0], after.tmp_tgl_2[0]],
            [before.tmp_tgl_2[1], after.tmp_tgl_2[1]],
            [before.tmp_tgl_2[2], after.tmp_tgl_2[2]],
            [before.tmp_tgl_2[3], after.tmp_tgl_2[3]]
        ]
        noon = before.prediction_timestamp.replace(hour=20)
        function = interp1d(x_axis, y_axis, kind='linear')
        # interpolate by time
        interpolated_noon_value = function(noon.timestamp())
        # interpolate by location
        interpolated_value = griddata(points, interpolated_noon_value, target_coordinate, method='linear')
        return interpolated_value[0]
    return None

    # for prediction, run in query:
    # print('for {} prediction:{} run:{}'.format(weather_date,
    #    prediction.prediction_timestamp, run.prediction_run_timestamp))


def match_predictions_with_actuals(session, actuals, grid, points, target_coordinate):
    actual_values = []
    predicted_values = []

    start_date = None
    end_date = None

    # we'll limit to a weeks worth of data to learn from

    for actual in actuals:
        result = most_recent_model_run(session, grid, actual.weather_date)
        if result is not None:
            if start_date is None:
                start_date = actual.weather_date
            end_date = actual.weather_date
            delta = actual.weather_date - start_date
            if delta.days > 2:
                # logger.info('stopped learning!')
                break
            prediction, run = result
            # interpolate grid location
            interpolated_value = griddata(points, prediction.tmp_tgl_2,
                                          target_coordinate, method='linear')
            actual_values.append(actual.temperature)
            # we take into account the model value for temperature, and the hour of the day
            predicted_values.append([interpolated_value[0], actual.weather_date.hour])

    # logger.info('data range: {} {} ({} samples)'.format(start_date, end_date, len(predicted_values)))

    #
    x = np.array(predicted_values)
    y = np.array(actual_values)
    return x, y, start_date, end_date


def main():
    session = get_session()
    stations = get_stations_sync()
    station_count = 0

    overall_machine_count = 0
    overall_human_count = 0

    with open('machine_all_stations.csv', 'w') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['station', 'date', 'actual', 'forecast', 'model', 'machine'])

        for station in stations:
            station_count += 1
            machine_count = 0
            human_count = 0
            tie_count = 0
            best_machine_estimate = math.inf
            worst_machine_estimate = 0
            best_human_estimate = math.inf
            worst_human_estimate = 0

            # logger.info('processing %s - %s', station['code'], station['name'])

            # logger.info('get actuals...')
            actuals = get_actuals(session, station['code'])

            # logger.info('get grid...')
            grid = get_coordinate_grid(session, station['lat'], station['long'])
            poly = to_shape(grid.geom)
            points = list(poly.exterior.coords)[:-1]
            target_coordinate = [(station['long'], station['lat'])]

            # for every actual, let's get the most recent prediction.
            # logger.info('get predicted values for actuals')
            x, y, start_date, end_date = match_predictions_with_actuals(
                session, actuals, grid, points, target_coordinate)

            if len(x) == 0:
                logger.info('insufficient data - skipping {}({})'.format(station['name'], station['code']))
            else:
                # create model and fit it
                # logger.info('doing model fit with {} data points'.format(len(x)))
                model = LinearRegression()
                model.fit(x, y)

                r_sq = model.score(x, y)
                # we want 1 for coefficient of determination, as it indicates a linear relationship.
                # logger.info('coefficient of determination: %s', r_sq)
                # logger.info('intercept: %s', model.intercept_)
                # logger.info('slope: %s', model.coef_)

                # ok - grand - we have a model, now let's make some predictions.
                # to be fair, we exclude data we used to learn.
                noon_forecasts = get_noon_forecasts(session, station['code'], end_date)
                noon_forecasts = extract_one_day_forecast(noon_forecasts)

                # logger.info('there are {} noon_forecasts'.format(len(noon_forecasts)))

                comparison_count = 0
                for forecast in noon_forecasts:
                    # get an appropriate model prediction for this forecast
                    # get the most recent model run for this forecast
                    prediction = get_noon_model_prediction(
                        session, grid, forecast.weather_date, points, target_coordinate)
                    if prediction:
                        actual = get_actual(session, station['code'], forecast.weather_date)
                        if actual:
                            comparison_count += 1
                            machine = model.predict([[prediction, forecast.weather_date.hour]])
                            # who is closer?
                            machine_delta = abs(round(machine[0], 1) - actual.temperature)
                            if best_machine_estimate > machine_delta:
                                best_machine_estimate = machine_delta
                            if worst_machine_estimate < machine_delta:
                                worst_machine_estimate = machine_delta
                            human_delta = abs(forecast.temperature - actual.temperature)
                            if best_human_estimate > human_delta:
                                best_human_estimate = human_delta
                            if worst_human_estimate < human_delta:
                                worst_human_estimate = human_delta
                            message = "It's a tie!"
                            if human_delta < machine_delta:
                                # human wins
                                message = "Human wins."
                                human_count += 1
                            elif machine_delta < human_delta:
                                # machine wins
                                message = "Machine wins"
                                machine_count += 1
                            else:
                                tie_count += 1

                            writer.writerow([station['code'], forecast.weather_date.isoformat(), actual.temperature, forecast.temperature,
                                             prediction, machine[0]])
                            # print('{} : forecast: {}, model prediction: {}, machine: {}, actual: {} ; {}'.format(
                            #     forecast.weather_date,
                            #     forecast.temperature,
                            #     round(prediction, 1),
                            #     round(machine[0], 1),
                            #     actual.temperature,
                            #     message))

                if comparison_count == 0:
                    logger.info('no data to compare for %s(%s)', station['name'], station['code'])
                else:
                    overall_machine_count += machine_count
                    overall_human_count += human_count
                    print('{} ({}): machines: {}, humans: {}'.format(
                        station['name'], station['code'], machine_count, human_count))
                    # print('worst human estimate, off by: {}'.format(round(worst_human_estimate, 1)))
                    # print('best human estimate, off by: {}'.format(best_human_estimate))
                    # print('worst machine estimate, off by: {}'.format(round(worst_machine_estimate, 1)))
                    # print('best machine estimate, off by: {}'.format(best_machine_estimate))
                    # if station_count > 2:
                    # break
            print('overall - machines: {}, humans: {}'.format(overall_machine_count, overall_human_count))


if __name__ == '__main__':
    main()
