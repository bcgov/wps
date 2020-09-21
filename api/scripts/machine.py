import logging
from datetime import timedelta
import numpy as np
import math
import matplotlib.pyplot as plt
import csv
from matplotlib.ticker import MultipleLocator
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from scipy.interpolate import griddata, interp1d
from geoalchemy2.shape import to_shape
from sqlalchemy import extract
from app import configure_logging
from app.stations import get_stations_sync

from app.db.database import get_write_session
from app.db.models import (
    HourlyActual, NoonForecast, PredictionModelGridSubset, ModelRunGridSubsetPrediction, PredictionModelRunTimestamp)


configure_logging()


logger = logging.getLogger()


use_hour = True


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


def interpolate_value(x_axis, noon, before, after, points, target_coordinate):
    y_axis = [
        [before[0], after[0]],
        [before[1], after[1]],
        [before[2], after[2]],
        [before[3], after[3]]
    ]
    function = interp1d(x_axis, y_axis, kind='linear')
    # interpolate by time.
    interpolated_noon_value = function(noon.timestamp())
    # interpolate by location.
    interpolated_value = griddata(
        points, interpolated_noon_value, target_coordinate, method='linear')
    return interpolated_value[0]


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

        # logger.info('for forecast: %s, using model %s',
        # weather_date, query[0][1].prediction_run_timestamp)

        # x-axis is the timestamp
        x_axis = (before.prediction_timestamp.timestamp(),
                  after.prediction_timestamp.timestamp())

        noon = before.prediction_timestamp.replace(hour=20)
        temperature = interpolate_value(
            x_axis, noon, before.tmp_tgl_2, after.tmp_tgl_2, points, target_coordinate)
        rh = interpolate_value(
            x_axis, noon, before.rh_tgl_2, after.rh_tgl_2, points, target_coordinate)
        return {
            'temperature': temperature,
            'rh': rh
        }
    return None


def match_predictions_with_actuals(session, actuals, grid, points, target_coordinate):
    actual_temperature_values = []
    actual_rh_values = []
    predicted_temperature_values = []
    predicted_rh_values = []

    start_date = None
    end_date = None

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
            interpolated_temperature_value = griddata(points, prediction.tmp_tgl_2,
                                                      target_coordinate, method='linear')
            interpolated_rh_value = griddata(
                points, prediction.rh_tgl_2, target_coordinate, method='linear')
            actual_temperature_values.append(actual.temperature)
            actual_rh_values.append(actual.relative_humidity)
            # we take into account the model value for temperature, and the hour of the day
            if use_hour:
                predicted_temperature_values.append(
                    [interpolated_temperature_value[0], calc_temp_hour(actual.weather_date)])
            else:
                predicted_temperature_values.append(
                    interpolated_temperature_value[0])
            # there's a correlation between temperature and relative humidity - so let's try to use that too.
            if use_hour:
                predicted_rh_values.append(
                    [interpolated_rh_value[0], calc_rh_hour(actual.weather_date)])
            else:
                predicted_rh_values.append(interpolated_rh_value[0])

    # logger.info('data range: {} {} ({} samples)'.format(start_date, end_date, len(predicted_values)))

    #
    data = {
        'temperature': {
            'x': np.array(predicted_temperature_values),
            'y': np.array(actual_temperature_values)
        },
        'rh': {
            'x': np.array(predicted_rh_values),
            'y': np.array(actual_rh_values)
        }
    }
    return data, start_date, end_date


class Judge:
    def __init__(self, name):
        self.name = name
        self.machine_count = 0
        self.human_count = 0
        self.tie = 0

    def round(self, value):
        raise NotImplementedError()

    def adjudicate(self, machine, human, observed):
        machine_delta = abs(self.round(machine) - observed)
        human_delta = abs(human-observed)
        if human_delta < machine_delta:
            self.human_count += 1
        elif machine_delta < human_delta:
            self.machine_count += 1
        else:
            self.tie += 1

    def __str__(self):
        return '{} judge: machines={}, humans={}, tie={}'.format(
            self.name, self.machine_count, self.human_count, self.tie)


class TemperatureJudge(Judge):

    def round(self, value):
        return round(value*2)/2


class RHJudge(Judge):
    def round(self, value):
        return round(value, 0)


def get_polynomial():
    return PolynomialFeatures(degree=2, include_bias=False)


def calc_rh_hour(timestamp):
    """
    20h00 UTC is solar noon in BC.
    22h00 UTC is 14h00 in BC.
    For some reason I don't understand there's correlation here.
    """
    return abs(((timestamp.hour + 2) % 24) - 12)


def calc_temp_hour(timestamp):
    """
    20h00 is solar noon in BC. (20h00 utc, -8 is 12 pacific, noon)
    8 hours after noon, is 20h00 PST, or 04h00 UTC
    for some reason, we get the highest temperature score if we make this the midpoint.
    I don't understand.
    """
    return abs(((timestamp.hour + 8) % 24) - 12)


# def calc_hour(timestamp):
#     # the hour is in utc
#     # 20h00 is noon, but the warmest part of the day is 5 hours later
#     # 20h00 + 5 = 01h00
#     # so 01h00 is the warmest really, but that in the middle, by adding 11
#     # so we can find the distance from warmest part, by adding 11, and then subtracting 12.
#     # so really, subtracting 1 gives us the distance from warmest part?
#     return abs(((timestamp.hour - 8) % 24) - 12)
#     # return timestamp.hour


def main():
    session = get_write_session()
    stations = get_stations_sync()
    station_count = 0

    overall_machine_count = {
        'temperature': 0,
        'rh': 0
    }
    overall_human_count = {
        'temperature': 0,
        'rh': 0
    }
    overall_tie_count = {
        'temperature': 0,
        'rh': 0
    }

    overall_temp_error = {
        'machine': [],
        'model': [],
        'human': []
    }
    overall_rh_error = {
        'machine': [],
        'model': [],
        'human': []
    }

    polynomial = False

    with open('machine_all_stations.csv', 'w') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['station', 'date',
                         'observed_temp', 'forecast_temp', 'model_temp', 'machine_temp',
                         'observed_rh', 'forecast_rh', 'model_rh', 'machine_rh',
                         'forecast_temp_error', 'model_temp_error', 'machine_temp_error',
                         'forecast_rh_error', 'model_rh_error', 'machine_rh_error'])

        for station in stations:
            # if station['code'] != '322':
            #     continue
            station_count += 1
            temp_judge = TemperatureJudge('temperature')
            rh_judge = RHJudge('relative humidity')

            logger.info('processing %s - %s', station['code'], station['name'])

            # logger.info('get actuals...')
            actuals = get_actuals(session, station['code'])

            # logger.info('get grid...')
            grid = get_coordinate_grid(
                session, station['lat'], station['long'])
            poly = to_shape(grid.geom)
            points = list(poly.exterior.coords)[:-1]
            target_coordinate = [(station['long'], station['lat'])]

            # for every actual, let's get the most recent prediction.
            # logger.info('get predicted values for actuals')
            data, start_date, end_date = match_predictions_with_actuals(
                session, actuals, grid, points, target_coordinate)

            if len(data['temperature']['x']) == 0:
                logger.info(
                    'insufficient data - skipping {}({})'.format(station['name'], station['code']))
            else:
                # create model and fit it
                logger.info(
                    'doing model fit with {} data points ({}-{})'.format(
                        len(data['temperature']['x']),
                        start_date, end_date))

                temperature_model = LinearRegression()
                x = data['temperature']['x']
                if polynomial:
                    x = get_polynomial().fit_transform(x)
                if not use_hour:
                    x = x.reshape((-1, 1))
                temperature_model.fit(x, data['temperature']['y'])

                rh_model = LinearRegression()
                x = data['rh']['x']
                if polynomial:
                    x = get_polynomial().fit_transform(x)
                if not use_hour:
                    x = x.reshape((-1, 1))

                rh_model.fit(x, data['rh']['y'])

                r_sq = temperature_model.score(x, data['temperature']['y'])
                # we want 1 for coefficient of determination, as it indicates a linear relationship.
                # logger.info('coefficient of determination: %s', r_sq)
                # logger.info('intercept: %s', temperature_model.intercept_)
                # logger.info('slope: %s', temperature_model.coef_)

                # ok - grand - we have a temperature_model, now let's make some predictions.
                # to be fair, we exclude data we used to learn.
                noon_forecasts = get_noon_forecasts(
                    session, station['code'], end_date)
                noon_forecasts = extract_one_day_forecast(noon_forecasts)

                # logger.info('there are {} noon_forecasts'.format(len(noon_forecasts)))

                comparison_count = 0
                for forecast in noon_forecasts:
                    # get an appropriate temperature_model prediction for this forecast
                    # get the most recent model run for this forecast
                    prediction = get_noon_model_prediction(
                        session, grid, forecast.weather_date, points, target_coordinate)
                    if prediction:
                        actual = get_actual(
                            session, station['code'], forecast.weather_date)
                        if actual:
                            comparison_count += 1
                            if use_hour:
                                x = [[prediction['temperature'],
                                      calc_temp_hour(forecast.weather_date)]]
                            else:
                                x = np.array([prediction['temperature']
                                              ]).reshape((-1, 1))
                            if polynomial:
                                x = get_polynomial().fit_transform(x)

                            machine = temperature_model.predict(x)
                            if use_hour:
                                x = [[prediction['rh'], calc_rh_hour(
                                    forecast.weather_date)]]
                            else:
                                x = np.array([prediction['rh']]
                                             ).reshape((-1, 1))
                            if polynomial:
                                x = get_polynomial().fit_transform(x)
                            machine_rh = rh_model.predict(x)
                            # who is closer?
                            temp_judge.adjudicate(
                                machine[0], forecast.temperature, actual.temperature)
                            rh_judge.adjudicate(
                                machine_rh[0], forecast.relative_humidity, actual.relative_humidity)

                            forecast_temp_error = abs(
                                actual.temperature - forecast.temperature)
                            model_temp_error = abs(
                                actual.temperature - prediction['temperature'])
                            machine_temp_error = abs(
                                actual.temperature - machine[0])
                            forecast_rh_error = abs(
                                actual.relative_humidity - forecast.relative_humidity)
                            model_rh_error = abs(
                                actual.relative_humidity - prediction['rh'])
                            machine_rh_error = abs(
                                actual.relative_humidity - machine_rh[0])

                            overall_temp_error['machine'].append(
                                machine_temp_error)
                            overall_temp_error['model'].append(
                                model_temp_error)
                            overall_temp_error['human'].append(
                                forecast_temp_error)
                            overall_rh_error['machine'].append(
                                machine_rh_error)
                            overall_rh_error['model'].append(model_rh_error)
                            overall_rh_error['human'].append(forecast_rh_error)

                            row = [
                                station['code'], forecast.weather_date.isoformat(),
                                actual.temperature, forecast.temperature,
                                prediction['temperature'], machine[0],
                                actual.relative_humidity, forecast.relative_humidity, prediction[
                                    'rh'], machine_rh[0],
                                forecast_temp_error, model_temp_error, machine_temp_error,
                                forecast_rh_error, model_rh_error, machine_rh_error
                            ]
                            writer.writerow(row)
                            # print('{} : forecast: {}, model prediction: {}, machine: {}, actual: {} ; {}'.format(
                            #     forecast.weather_date,
                            #     forecast.temperature,
                            #     round(prediction, 1),
                            #     round(machine[0], 1),
                            #     actual.temperature,
                            #     message))

                if comparison_count == 0:
                    logger.info('no data to compare for %s(%s)',
                                station['name'], station['code'])
                else:
                    overall_machine_count['temperature'] += temp_judge.machine_count
                    overall_human_count['temperature'] += temp_judge.human_count
                    overall_tie_count['temperature'] += temp_judge.tie
                    overall_machine_count['rh'] += rh_judge.machine_count
                    overall_human_count['rh'] += rh_judge.human_count
                    overall_tie_count['rh'] += rh_judge.tie

                    print('{} ({}): {}, {}'.format(
                        station['name'], station['code'], temp_judge, rh_judge))
                    # print('worst human estimate, off by: {}'.format(round(worst_human_estimate, 1)))
                    # print('best human estimate, off by: {}'.format(best_human_estimate))
                    # print('worst machine estimate, off by: {}'.format(round(worst_machine_estimate, 1)))
                    # print('best machine estimate, off by: {}'.format(best_machine_estimate))
                    # if station_count > 2:
                    # break
                # break
            print(
                'overall - machines: {}, humans: {}, tie: {}'.format(overall_machine_count, overall_human_count, overall_tie_count))

            machine_t_e = np.average(overall_temp_error['machine'])
            model_t_e = np.average(overall_temp_error['model'])
            human_t_e = np.average(overall_temp_error['human'])

            machine_r_e = np.average(overall_rh_error['machine'])
            model_r_e = np.average(overall_rh_error['model'])
            human_r_e = np.average(overall_rh_error['human'])

            print('temperature error')
            print('machine: {} ; model: {} ; human: {}'.format(
                machine_t_e, model_t_e, human_t_e))
            print('rh error')
            print('machine: {} ; model: {} ; human: {}'.format(
                machine_r_e, model_r_e, human_r_e))


if __name__ == '__main__':
    main()
