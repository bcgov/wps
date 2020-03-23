from os import getenv
from statistics import mean
import json
from typing import List, Dict
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Form, status, HTTPException
import os

api_info = '''
    Description: API for the PSU FWI Calculator

    Warranty Disclaimer:

    This 90th Percentile Forest Fire Weather Index(FWI) system software
    and related documentation is provided as a public service by the
    Government of British Columbia, Box 9411, Victoria, British
    Columbia, Canada V8W 9V1.

    This 90th Percentile Forest Fire Weather Index(FWI) system software
    and related documentation are provided \"as is\" without
    warranty of any kind, whether express or implied. Users of this
    software and documentation do so at their own risk. All implied
    warranties, including, without limitation, implied warranties of
    merchantability, fitness for a particular purpose, and
    non - infringement, are hereby expressly disclaimed. Links and
    references to any other websites or software are provided for
    information only and listing shall not be taken as endorsement of
    any kind.

    The Government of British Columbia is not responsible for the
    content or reliability of any linked software and websites and does
    not endorse the content, products, services or views expressed
    within them. It is the responsibility of all persons who use 90th
    Percentile Forest Fire Weather Index(FWI) system software and
    related documentation to independently confirm the accuracy of the
    data, information, or results obtained through their use.

    Limitation of Liabilities Under no circumstances will the Government
    of British Columbia be liable to any person or business entity for
    any direct, indirect, special, incidental, consequential, or other
    damages based on any use of this software and documentation or any
    other software to which this site is linked, including, without
    limitation, any lost profits, business interruption, or loss of
    programs or information, even if the Government of British Columbia
    has been specifically advised of the possibility of such damages.'''


class Season(BaseModel):
    start_month: int
    start_day: int
    end_month: int
    end_day: int


class YearRange(BaseModel):
    start: int
    end: int


class PercentileRequest(BaseModel):
    stations: List[str]
    percentile: int
    year_range: YearRange


class WeatherStation(BaseModel):
    code: int
    name: str


class StationSummary(BaseModel):
    FFMC: float
    ISI: float
    BUI: float
    season: Season
    years: List[int]
    station: WeatherStation


class MeanValues(BaseModel):
    FFMC: float = None
    ISI: float = None
    BUI: float = None


class CalculatedResponse(BaseModel):
    stations: Dict[int, StationSummary] = {}
    mean_values: MeanValues = None
    year_range: YearRange
    percentile: int


class WeatherStations(BaseModel):
    weather_stations: List[WeatherStation]


app = FastAPI(
    title="Predictive Services Fire Weather Index Calculator",
    description=api_info,
    version="0.0.0"
)

origins = getenv('ORIGINS')

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get('/stations', response_model=WeatherStations)
async def get_stations():
    """ Return a list of fire weather stations.
    """
    return WeatherStations.parse_file('data/weather_stations.json')


@app.post('/percentiles/', response_model=CalculatedResponse)
async def get_percentiles(request: PercentileRequest):
    """ Return 90% FFMC, 90% ISI, 90% BUI etc. for a given set of fire stations for a given period of time.
    """
    # NOTE: percentile is ignored, all responses overriden to match
    # pre-calculated values; 90th percentile
    year_range_start = request.year_range.start
    year_range_end = request.year_range.end

    # Error Code: 400 (Bad request)
    if len(request.stations) == 0 or request.stations is None:
        raise HTTPException(status_code=400)

    if not os.path.exists('data/{}-{}'.format(year_range_start, year_range_end)):
        raise HTTPException(status_code=400)

    response = CalculatedResponse(
        percentile=90,
        year_range=YearRange(
            start=year_range_start,
            end=year_range_end))
    bui = []
    isi = []
    ffmc = []
    for station in request.stations:
        try:
            summary = StationSummary.parse_file(
                'data/{}-{}/{}.json'.format(year_range_start, year_range_end, station))
        except BaseException:
            raise HTTPException(status_code=404, detail='Weather data not found')
        bui.append(summary.BUI)
        isi.append(summary.ISI)
        ffmc.append(summary.FFMC)
        response.stations[station] = summary
    response.mean_values = MeanValues()
    response.mean_values.BUI = mean(bui)
    response.mean_values.ISI = mean(isi)
    response.mean_values.FFMC = mean(ffmc)
    return response
