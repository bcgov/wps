from app.weather_models.interpolate import construct_interpolated_noon_prediction, SCALAR_MODEL_VALUE_KEYS_FOR_INTERPOLATION, interpolate_between_two_points
from datetime import datetime
from app.db.models.weather_models import ModelRunPrediction


def generate_model_run_prediction(prediction_datetime: datetime, weather_values: float) -> ModelRunPrediction:
    model_prediction = ModelRunPrediction(
                            prediction_timestamp=prediction_datetime,
                            tmp_tgl_2=weather_values,
                            rh_tgl_2=weather_values,
                            apcp_sfc_0=weather_values,
                            wind_tgl_10=weather_values,
                            wdir_tgl_10=weather_values
                            )
    return model_prediction


def test_construct_interpolated_noon_prediction():
    prediction_a_timestamp = datetime(2024, 5, 1, 18, 0, 0)
    prediction_b_timestamp = datetime(2024, 5, 1, 21, 0, 0)
    prediction_a = generate_model_run_prediction(prediction_a_timestamp, 1.1)
    prediction_b = generate_model_run_prediction(prediction_b_timestamp, 4.4)
    
    noon_prediction = construct_interpolated_noon_prediction(prediction_a, prediction_b, SCALAR_MODEL_VALUE_KEYS_FOR_INTERPOLATION)
    assert noon_prediction.prediction_timestamp.hour == 20
    assert noon_prediction.apcp_sfc_0 is not None
    assert noon_prediction.rh_tgl_2 is not None
    assert noon_prediction.wdir_tgl_10 is not None
    assert noon_prediction.wind_tgl_10 is not None
    assert noon_prediction.tmp_tgl_2 is not None
