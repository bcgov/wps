from datetime import timedelta
import numpy as np
from sklearn.linear_model import LinearRegression
from app.db.database import get_session
from app.stations import get_stations_sync
from app.models import ModelEnum
from app.db.crud import (get_hourly_actuals,
                         get_most_recent_model_run, LATLON_15X_15, get_weather_station_model_predictions,
                         get_closest_model_run, get_prediction_model, get_weather_station_model_prediction)
from app.time_utils import get_pst_now


def main():
    stations = get_stations_sync()
    now = get_pst_now()
    start_date = now - timedelta(days=10)
    session = get_session()
    model = get_prediction_model(session, ModelEnum.GDPS, LATLON_15X_15)
    print('model: {}'.format(model))
    for station in stations:
        # prepare data
        actuals = get_hourly_actuals(session, [station['code']], start_date)
        x = []
        y = []
        for actual in actuals:
            model_run = get_closest_model_run(session, model.id, actual.weather_date)
            prediction = get_weather_station_model_prediction(
                session, station['code'], model_run.id, actual.weather_date)
            if prediction is not None:
                print('actual: {}'.format(actual.weather_date))
                print('closest model run: {}'.format(model_run))
                print('found prediction: {}'.format(prediction))
                x.append(prediction.tmp_tgl_2)
                y.append(actual.temperature)

        x = np.array(x).reshape((-1, 1))
        y = np.array(y)

        # create model and fit it
        model = LinearRegression()
        model.fit(x, y)

        # predict the actual weather using the linear model applied to the weather model prediction
        most_recent_run = get_most_recent_model_run(
            session, ModelEnum.GDPS, LATLON_15X_15)
        predictions = get_weather_station_model_predictions(session, station['code'], most_recent_run.id)
        x_pred = []
        y_pred = []
        for prediction in predictions:
            x_pred.append(prediction.prediction_timestamp)
            y_pred.append([prediction.tmp_tgl_2])
        print(y_pred)
        y_pred = model.predict(y_pred)

        for timestamp, prediction, model_prediction in zip(x_pred, y_pred, predictions):
            # Store our machine learning prediction
            print('{}: {} -> {}'.format(timestamp, model_prediction.tmp_tgl_2, prediction))
            # TODO: store it here

        break


if __name__ == '__main__':
    main()
