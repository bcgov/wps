from datetime import date, datetime, timezone
from enum import Enum
import logging
import math
from statistics import mean, quantiles
from typing import List
from fastapi import APIRouter, Response, Depends, status, HTTPException

from app.db.crud.skill import get_skill_score_data
from app.db.database import get_read_session_scope
from app.schemas.shared import StationsRequest
from app.schemas.skill import (
    DaySkillData,
    DaySkillStats,
    ModelSkillData,
    ModelSkillStats,
    SkillData,
    SkillStats,
    StationSkillData,
    WeatherParamEnum,
    WeatherParamSkillData,
    WeatherParamSkillStats,
)
from app.utils.time import get_hour_20_from_date
from app.weather_models import ModelEnum


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/skill")  # , dependencies=[Depends(authentication_required), Depends(audit)])


WEATHER_PARAM_LIST = [WeatherParamEnum.PRECIP, WeatherParamEnum.RH, WeatherParamEnum.TEMP, WeatherParamEnum.WIND_DIR, WeatherParamEnum.WIND_SPEED]
MODEL_LIST = [ModelEnum.HRDPS, ModelEnum.RDPS, ModelEnum.GDPS, ModelEnum.NAM, ModelEnum.GFS]


@router.post("/score2/{start_date}/{days}")
async def get_weather_model_skill2(start_date: date, days: int, request: StationsRequest, response: Response):
    with get_read_session_scope() as db_session:
        results = get_skill_score_data(db_session, start_date, days, request.stations)

    samples = create_empty_skill_samples_dict2(days)
    for model, prediction_timestamp, model_run_timestamp, forecast_temp, actual_temp, bias_adjusted_temperature, station_code in results:
        diff = prediction_timestamp - model_run_timestamp
        if diff.days < days and forecast_temp is not None and actual_temp is not None:
            if station_code not in samples[WeatherParamEnum.TEMP][diff.days][model]:
                samples[WeatherParamEnum.TEMP][diff.days][model][station_code] = []
            samples[WeatherParamEnum.TEMP][diff.days][model][station_code].append(forecast_temp - actual_temp)
            # samples[WeatherParamEnum.RH][diff.days][model][station_code].append(forecast_rh - actual_rh)

    weatherParamSkillDataList = []
    for key, value in samples.items():
        daySkillDataList = []
        for key2, value2 in value.items():
            modelSkillDataList = []
            for key3, value3 in value2.items():
                stationSkillDataList = []
                for key4, value4 in value3.items():
                    stationData = StationSkillData(stationCode=key4, skillData=value4)
                    stationSkillDataList.append(stationData)
                modelSkillData = ModelSkillData(model=key3, stationSkillData=stationSkillDataList)
                modelSkillDataList.append(modelSkillData)
            daySkillData = DaySkillData(day=key2, modelSkillData=modelSkillDataList)
            daySkillDataList.append(daySkillData)
        weatherParamSkillData = WeatherParamSkillData(weatherParam=key, daySkillData=daySkillDataList)
        weatherParamSkillDataList.append(weatherParamSkillData)

    return SkillData(skillData=weatherParamSkillDataList)


@router.post("/score/{start_date}/{days}")
async def get_weather_model_skill(start_date: date, days: int, request: StationsRequest, response: Response):
    with get_read_session_scope() as db_session:
        results = get_skill_score_data(db_session, start_date, days, request.stations)

    # results = [
    #     ("HRDPS", datetime(2024, 10, 12, 20, 0, tzinfo=timezone.utc), datetime(2024, 10, 11, 12, 0, tzinfo=timezone.utc), 16.0, 15.8, 390),
    #     ("HRDPS", datetime(2024, 10, 12, 20, 0, tzinfo=timezone.utc), datetime(2024, 10, 12, 12, 0, tzinfo=timezone.utc), 14.9, 15.8, 390),
    #     ("HRDPS", datetime(2024, 10, 13, 20, 0, tzinfo=timezone.utc), datetime(2024, 10, 12, 12, 0, tzinfo=timezone.utc), 17.4, 16.8, 390),
    #     ("HRDPS", datetime(2024, 10, 13, 20, 0, tzinfo=timezone.utc), datetime(2024, 10, 13, 12, 0, tzinfo=timezone.utc), 16.7, 16.8, 390),
    #     ("HRDPS", datetime(2024, 10, 14, 20, 0, tzinfo=timezone.utc), datetime(2024, 10, 13, 12, 0, tzinfo=timezone.utc), 17.1, 14.6, 390),
    #     ("HRDPS", datetime(2024, 10, 14, 20, 0, tzinfo=timezone.utc), datetime(2024, 10, 14, 12, 0, tzinfo=timezone.utc), 15.4, 14.6, 390),
    # ]
    # samples = {ModelEnum.HRDPS: dict(zip(range(0, days), (get_empty_weather_variable_dict() for x in range(0, days))))}
    samples = create_empty_skill_samples_dict(days)
    for model, prediction_timestamp, model_run_timestamp, forecast_temp, actual_temp, station_code in results:
        diff = prediction_timestamp - model_run_timestamp
        if diff.days < days and forecast_temp is not None and actual_temp is not None:
            # samples[model][diff.days]["temp"].append(forecast_temp - actual_temp)
            samples[WeatherParamEnum.TEMP][diff.days][model].append(forecast_temp - actual_temp)

    weatherParamSkillStats = []
    for key, value in samples.items():
        daySkillStats = []
        for key2, value2 in value.items():
            modelSkillStats = []
            for key3, value3 in value2.items():
                if len(value3) < 3:
                    continue
                quartiles = quantiles(value3, n=4)
                modelSkillStat = ModelSkillStats(
                    max=max(value3),
                    mean=mean(value3),
                    median=round(quartiles[1], 1),
                    min=min(value3),
                    rmse=calculate_rmse(value3),
                    model=key3,
                    percentile25=round(quartiles[0], 1),
                    percentile75=round(quartiles[2], 1),
                    raw=value3,
                )
                modelSkillStats.append(modelSkillStat)
            daySkillStat = DaySkillStats(day=key2, modelSkillStats=modelSkillStats)
            daySkillStats.append(daySkillStat)
        weatherParamSkillStat = WeatherParamSkillStats(weatherParam=key, daySkillStats=daySkillStats)
        weatherParamSkillStats.append(weatherParamSkillStat)

    return SkillStats(skillStats=weatherParamSkillStats)


# def get_empty_weather_variable_dict():
#     return {"precip": [], "rh": [], "temp": [], "wind_direction": [], "wind_speed": []}


def create_empty_skill_samples_dict(days: int):
    skill_samples_dict = {}
    for weather_param in WEATHER_PARAM_LIST:
        skill_samples_dict[weather_param.value] = dict(zip(range(0, days), (create_empty_model_dict() for _ in range(0, days))))
    return skill_samples_dict
    # return {WeatherParamEnum.TEMP.value: dict(zip(range(0, days), (create_empty_model_dict() for _ in range(0, days))))}


def create_empty_model_dict():
    return {model: [] for model in MODEL_LIST}


def calculate_rmse(values: List[float]):
    sum_of_squares = sum(value * value for value in values)
    return math.sqrt(sum_of_squares / len(values))


def create_empty_skill_samples_dict2(days: int):
    skill_samples_dict = {}
    for weather_param in WEATHER_PARAM_LIST:
        skill_samples_dict[weather_param.value] = dict(zip(range(0, days), (create_empty_model_dict2() for _ in range(0, days))))
    return skill_samples_dict
    # return {WeatherParamEnum.TEMP.value: dict(zip(range(0, days), (create_empty_model_dict() for _ in range(0, days))))}


def create_empty_model_dict2():
    return {model: {} for model in MODEL_LIST}
