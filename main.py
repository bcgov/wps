from os import getenv
from statistics import mean
import json
from typing import List

from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Form


class Season(BaseModel):
    start_month: int
    start_day: int
    end_month: int
    end_day: int


class YearRange(BaseModel):
    start: int
    end: int


class StationSummary(BaseModel):
    FFMC: float
    ISI: float
    BUI: float
    season: Season
    year_range: YearRange


class CalculatedResponse(BaseModel):
    percentile: int
    stations: List[StationSummary] = []
    FFMC: float = None
    ISI: float = None
    BUI: float = None
    year_range: YearRange


class WeatherStation(BaseModel):
    code: int
    name: str


class WeatherStations(BaseModel):
    weather_stations: List[WeatherStation]


app = FastAPI(
    title="Predictive Services Fire Weather Index Calculator",
    description="API for the PSU FWI Calculator",
    version="0.0.0"
)

origins = getenv('ORIGINS')

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get('/stations', response_model=WeatherStations)
async def get_stations():
    """ Return a list of fire weather stations.
    """
    return WeatherStations.parse_file('data/weather_stations.json')


@app.post('/percentiles/', response_model=CalculatedResponse)
async def get_percentiles(*, stations: List[str] = Form(...), percentile: int = Form(...),
                          start_year: int = Form(...), end_year: int = Form(...)):
    """ Return 90% FFMC, 90% ISI, 90% BUI etc. for a given set of fire stations for a given period of time.
    """
    # NOTE: percentile, start_year and end_year input is ignored, all responses overriden to match
    # pre-calculated values; 90th percentile, start year 2010, end year 2019
    response = CalculatedResponse(percentile=90, year_range=YearRange(start=2010, end=2019))
    bui = []
    isi = []
    ffmc = []
    for station in stations[0].split(','):
        summary = StationSummary.parse_file('data/{}.json'.format(station))
        bui.append(summary.BUI)
        isi.append(summary.ISI)
        ffmc.append(summary.FFMC)
        response.stations.append(summary)
    response.BUI = mean(bui)
    response.ISI = mean(isi)
    response.FFMC = mean(ffmc)
    return response
