"""This module contains pydantic models for skill scoring"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.weather_models import ModelEnum


class WeatherParamEnum(str, Enum):
    """Enumerator for weather variables"""

    PRECIP = "precip"
    RH = "rh"
    TEMP = "temp"
    WIND_DIR = "wind_dir"
    WIND_SPEED = "wind_speed"


class ModelSkillStats(BaseModel):
    """Skill scoring data for a weather variable for a numerical weather model"""

    max: float
    mean: float
    min: float
    rmse: float
    model: ModelEnum
    percentile25: float
    percentile75: float
    raw: List[float]


class DaySkillStats(BaseModel):
    day: int
    modelSkillStats: List[ModelSkillStats]


class WeatherParamSkillStats(BaseModel):
    weatherParam: WeatherParamEnum
    daySkillStats: List[DaySkillStats]


class SkillStats(BaseModel):
    skillStats: Optional[List[WeatherParamSkillStats]]


class StationSkillData(BaseModel):
    stationCode: int
    skillData: List[float]


class ModelSkillData(BaseModel):
    model: ModelEnum
    stationSkillData: List[StationSkillData]


class DaySkillData(BaseModel):
    day: int
    modelSkillData: List[ModelSkillData]


class WeatherParamSkillData(BaseModel):
    weatherParam: WeatherParamEnum
    daySkillData: List[DaySkillData]


class SkillData(BaseModel):
    skillData: List[WeatherParamSkillData]
