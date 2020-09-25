""" This file used during machine learning experimentation - not worthy of being included on the main
branch.
"""
# pylint: disable-all
import logging
from collections import defaultdict
from datetime import timedelta
import numpy as np
import csv
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from scipy.interpolate import griddata, interp1d
from geoalchemy2.shape import to_shape
from app import configure_logging
from app.stations import get_stations_sync

from app.db.database import get_write_session
from app.db.models import (
    HourlyActual, NoonForecast, PredictionModelGridSubset, ModelRunGridSubsetPrediction, PredictionModelRunTimestamp)


configure_logging()


logger = logging.getLogger()


def get_actuals(session, station_code):
    return session.query(HourlyActual)\
        .filter(HourlyActual.station_code == station_code)\
        .filter(HourlyActual.temp_valid == True)\
        .filter(HourlyActual.rh_valid == True)\
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


def interpolate_values_by_time(x_axis, noon, before, after):
    y_axis = [
        [before[0], after[0]],
        [before[1], after[1]],
        [before[2], after[2]],
        [before[3], after[3]]
    ]
    function = interp1d(x_axis, y_axis, kind='linear')
    # interpolate by time.
    return function(noon.timestamp())


def interpolate_by_location(points, values, target_coordinate):
    return griddata(points, values, target_coordinate, method='linear')


def interpolate_value(x_axis, noon, before, after, points, target_coordinate):
    # interpolate by time.
    interpolated_noon_value = interpolate_values_by_time(
        x_axis, noon, before, after)
    # interpolate by location.
    interpolated_value = interpolate_by_location(
        points, interpolated_noon_value, target_coordinate)
    return interpolated_value[0]


def get_noon_model_prediction(session, grid, weather_date):
    """ 
    Create a quasi noon model prediction (global model doesn't
    actually have one!)
    """
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

        if query[0][1].id != query[1][1].id:
            raise Exception('expecting same model run')

        # logger.info('for forecast: %s, using model %s',
        # weather_date, query[0][1].prediction_run_timestamp)

        # x-axis is the timestamp
        x_axis = (before.prediction_timestamp.timestamp(),
                  after.prediction_timestamp.timestamp())

        noon = before.prediction_timestamp.replace(hour=20)
        temperature = interpolate_values_by_time(
            x_axis, noon, before.tmp_tgl_2, after.tmp_tgl_2)
        rh = interpolate_values_by_time(
            x_axis, noon, before.rh_tgl_2, after.rh_tgl_2)

        prediction = ModelRunGridSubsetPrediction()
        prediction.prediction_timestamp = noon
        prediction.tmp_tgl_2 = temperature
        prediction.rh_tgl_2 = rh

        return prediction, query[0][1]

    return None, None


class ModelData():

    def __init__(self):
        self.x = defaultdict(list)
        self.y = defaultdict(list)


class ModelDataCollection():

    def __init__(self):
        self.temperature = ModelData()
        self.rh = ModelData()


def match_predictions_with_actuals(session, actuals, grid, points, target_coordinate, days_of_samples):

    start_date = None
    end_date = None

    data = ModelDataCollection()
    for actual in actuals:
        if actual.weather_date.hour != 20:
            continue
        if actual.weather_date.hour == 20:
            result = get_noon_model_prediction(
                session, grid, actual.weather_date)
        else:
            result = most_recent_model_run(session, grid, actual.weather_date)
        if result is not None:
            if start_date is None:
                start_date = actual.weather_date
            end_date = actual.weather_date
            delta = actual.weather_date - start_date
            if delta.days >= days_of_samples:
                # logger.info('stopped learning!')
                break
            prediction, run = result
            # interpolate grid location
            interpolated_temperature_value = griddata(points, prediction.tmp_tgl_2,
                                                      target_coordinate, method='linear')
            interpolated_rh_value = griddata(
                points, prediction.rh_tgl_2, target_coordinate, method='linear')

            data.temperature.x[actual.weather_date.hour].append(
                interpolated_temperature_value[0])
            data.temperature.y[actual.weather_date.hour].append(
                actual.temperature)

            data.rh.x[actual.weather_date.hour].append(
                interpolated_rh_value[0])
            data.rh.y[actual.weather_date.hour].append(
                actual.relative_humidity)

    # convert to nice numpy arrays
    if end_date:
        for hour in range(24):
            if hour in data.temperature.x:
                data.temperature.x[hour] = np.array(data.temperature.x[hour])
                data.temperature.y[hour] = np.array(data.temperature.y[hour])
            if hour in data.rh.x:
                data.rh.x[hour] = np.array(data.rh.x[hour])
                data.rh.y[hour] = np.array(data.rh.y[hour])

    return data, start_date, end_date


class LinearModels():
    temperature = None
    rh = None


def create_models(data):
    models = defaultdict(LinearModels)
    for hour in range(24):
        if hour in data.temperature.x:
            if len(data.temperature.x[hour] >= 2):
                models[hour].temperature = LinearRegression()
                models[hour].temperature.fit(
                    data.temperature.x[hour].reshape((-1, 1)),
                    data.temperature.y[hour])
            else:
                logger.info('hour %s has %s samples for temperature',
                            hour, len(data.temperature.x[hour]))
        elif hour == 20:
            logger.info('no data for hour %s', hour)
        if hour in data.rh.x:
            if len(data.rh.x[hour] >= 2):
                models[hour].rh = LinearRegression()
                models[hour].rh.fit(
                    data.rh.x[hour].reshape((-1, 1)),
                    data.rh.y[hour])
    return models


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


def round_temperature(value):
    return round(value*2)/2


def round_rh(value):
    return round(value, 0)


class TemperatureJudge(Judge):

    def round(self, value):
        return round(value*2)/2


class RHJudge(Judge):
    def round(self, value):
        return round(value, 0)


def get_polynomial():
    return PolynomialFeatures(degree=2, include_bias=False)


def main(days_of_samples):
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
        'human': [],
        'machine_round': []
    }
    overall_rh_error = {
        'machine': [],
        'model': [],
        'human': [],
        'machine_round': []
    }

    with open('machine_all_stations_{}.csv'.format(days_of_samples), 'w') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['station', 'date',
                         'observed_temp', 'forecast_temp', 'model_temp', 'machine_temp',
                         'observed_rh', 'forecast_rh', 'model_rh', 'machine_rh',
                         'forecast_temp_error', 'model_temp_error', 'machine_temp_error',
                         'forecast_rh_error', 'model_rh_error', 'machine_rh_error'])

        for station in stations:
            # if station['code'] != '322':
            # continue
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
                session, actuals, grid, points, target_coordinate, days_of_samples)

            if end_date is None:
                logger.info('no data for %s', station['code'])
                continue

            models = create_models(data)

            if models[20].temperature is None:
                logger.info('no linear model for %s', station['code'])
                continue

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
                prediction, run = get_noon_model_prediction(
                    session, grid, forecast.weather_date)
                if prediction:
                    actual = get_actual(
                        session, station['code'], forecast.weather_date)
                    if actual:
                        comparison_count += 1

                        predicted_temperature = interpolate_by_location(
                            points, prediction.tmp_tgl_2, target_coordinate)
                        predicted_rh = interpolate_by_location(
                            points, prediction.rh_tgl_2, target_coordinate)

                        machine_temp = models[forecast.weather_date.hour].temperature.predict(
                            [predicted_temperature])
                        machine_rh = models[forecast.weather_date.hour].rh.predict([
                                                                                   predicted_rh])

                        temp_judge.adjudicate(
                            machine_temp[0], forecast.temperature, actual.temperature)
                        rh_judge.adjudicate(
                            machine_rh[0], forecast.relative_humidity, actual.relative_humidity)

                        forecast_temp_error = abs(
                            actual.temperature - forecast.temperature)
                        model_temp_error = abs(
                            actual.temperature - predicted_temperature[0])
                        machine_temp_error = abs(
                            actual.temperature - machine_temp[0])
                        machine_temp_round_error = abs(
                            actual.temperature - round_temperature(machine_temp[0]))
                        forecast_rh_error = abs(
                            actual.relative_humidity - forecast.relative_humidity)
                        model_rh_error = abs(
                            actual.relative_humidity - predicted_rh[0])
                        machine_rh_error = abs(
                            actual.relative_humidity - machine_rh[0])
                        machine_rh_round_error = abs(
                            actual.relative_humidity - round_rh(machine_rh[0]))

                        overall_temp_error['machine'].append(
                            machine_temp_error)
                        overall_temp_error['machine_round'].append(
                            machine_temp_round_error)
                        overall_temp_error['model'].append(
                            model_temp_error)
                        overall_temp_error['human'].append(
                            forecast_temp_error)
                        overall_rh_error['machine'].append(
                            machine_rh_error)
                        overall_rh_error['machine_round'].append(
                            machine_rh_round_error)
                        overall_rh_error['model'].append(model_rh_error)
                        overall_rh_error['human'].append(forecast_rh_error)

                        row = [
                            station['code'], forecast.weather_date.isoformat(),
                            actual.temperature, forecast.temperature,
                            predicted_temperature[0], machine_temp[0],
                            actual.relative_humidity, forecast.relative_humidity, predicted_rh[
                                0], machine_rh[0],
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
            machine_t_e_r = np.average(overall_temp_error['machine_round'])
            model_t_e = np.average(overall_temp_error['model'])
            human_t_e = np.average(overall_temp_error['human'])

            machine_r_e = np.average(overall_rh_error['machine'])
            machine_r_e_r = np.average(overall_rh_error['machine_round'])
            model_r_e = np.average(overall_rh_error['model'])
            human_r_e = np.average(overall_rh_error['human'])

            print('temperature error')
            print('machine: {} ; model: {} ; human: {}'.format(
                machine_t_e, model_t_e, human_t_e))
            print('rh error')
            print('machine: {} ; model: {} ; human: {}'.format(
                machine_r_e, model_r_e, human_r_e))

    machine_t_e = np.average(overall_temp_error['machine'])
    machine_t_e_r = np.average(overall_temp_error['machine_round'])
    model_t_e = np.average(overall_temp_error['model'])
    human_t_e = np.average(overall_temp_error['human'])

    machine_r_e = np.average(overall_rh_error['machine'])
    machine_r_e_r = np.average(overall_rh_error['machine_round'])
    model_r_e = np.average(overall_rh_error['model'])
    human_r_e = np.average(overall_rh_error['human'])

    return machine_t_e, machine_t_e_r, model_t_e, human_t_e, machine_r_e, machine_r_e_r, model_r_e, human_r_e


if __name__ == '__main__':
    with open('accuracy.csv', 'w') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['sample_size',
                         'machine_temp_error', 'machine_temp_error_round', 'model_temp_error', 'forecast_temp_error',
                         'machine_rh_error', 'machine_rh_error_round', 'model_rh_error', 'forecast_rh_error'])

        for days_of_samples in range(1, 24):
            machine_t_e, machine_t_e_r, model_t_e, human_t_e, machine_r_e, machine_r_e_r, model_r_e, human_r_e = main(
                days_of_samples)
            writer.writerow([days_of_samples,
                             machine_t_e, machine_t_e_r, model_t_e, human_t_e,
                             machine_r_e, machine_r_e_r, model_r_e, human_r_e])
            csv_file.flush()
