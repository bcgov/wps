""" This module contains pydandict schemas the HFI Calculator.
"""
from lib2to3.pgen2.token import OP
from typing import List, Mapping, Optional
from datetime import datetime, date
from pydantic import BaseModel
from app.schemas.shared import FuelType


class StationDaily(BaseModel):
    """ Station Daily metrics for HFI daily table """
    code: Optional[int] = None
    status: Optional[str] = None
    temperature: Optional[float] = None
    relative_humidity: Optional[float] = None
    wind_speed: Optional[float] = None
    wind_direction: Optional[float] = None
    grass_cure_percentage: Optional[float] = None
    precipitation: Optional[float] = None
    ffmc: Optional[float] = None
    dmc: Optional[float] = None
    dc: Optional[float] = None
    isi: Optional[float] = None
    bui: Optional[float] = None
    fwi: Optional[float] = None
    danger_class: Optional[int] = None
    observation_valid: Optional[bool] = None
    observation_valid_comment: Optional[str] = None
    rate_of_spread: Optional[float] = None
    hfi: Optional[float] = None
    intensity_group: Optional[int] = None
    sixty_minute_fire_size: Optional[float] = None
    fire_type: Optional[str] = None
    error: Optional[bool] = False
    error_message: Optional[str] = None
    date: Optional[datetime] = None
    last_updated: Optional[datetime] = None


required_daily_fields = ['temperature',
                         'relative_humidity',
                         'wind_speed',
                         'wind_direction',
                         'precipitation',
                         'intensity_group']


class StationDailyResponse(BaseModel):
    """ Response that includes list of station daily data."""
    dailies: List[StationDaily]


class ValidatedStationDaily(BaseModel):
    """
    Station daily with validity flag
    """
    daily: StationDaily
    valid: bool


class FireStartRange(BaseModel):
    """
    User facing label, value and lookup table of fire starts to prep level
    """
    label: str
    value: int
    lookup_table: Mapping[int, int]


lowest_fire_starts = FireStartRange(label='0-1', value=1, lookup_table={1: 1, 2: 1, 3: 2, 4: 3, 5: 4})
one_2_two_starts = FireStartRange(label='1-2', value=2, lookup_table={1: 1, 2: 2, 3: 3, 4: 4, 5: 5})
two_2_three_starts = FireStartRange(label='2-3', value=3, lookup_table={1: 2, 2: 3, 3: 4, 4: 5, 5: 6})
three_2_six_starts = FireStartRange(label='3-6', value=6, lookup_table={1: 3, 2: 4, 3: 5, 4: 6, 5: 6})
highest_fire_starts = FireStartRange(label='6+', value=7, lookup_table={1: 4, 2: 5, 3: 6, 4: 6, 5: 6})
all_ranges = [lowest_fire_starts, one_2_two_starts,
              two_2_three_starts, three_2_six_starts, highest_fire_starts]


class DailyResult(BaseModel):
    """
    Prep level, MIG, fire starts and station daily results for a day in a prep week
    """
    dateISO: str
    dailies: List[ValidatedStationDaily]
    fire_starts: FireStartRange
    mean_intensity_group: Optional[float]
    prep_level: Optional[float]


class PlanningAreaResult(BaseModel):
    """
    Mean prep level / max intensity group,
    dailies and validity status of station dailies in a planning area
    """
    all_dailies_valid: bool
    highest_daily_intensity_group: Optional[float]
    mean_prep_level: Optional[float]
    daily_results: List[DailyResult]


class WeatherStationProperties(BaseModel):
    """ HFI-relevant weather station properties """
    name: str
    elevation: int
    fuel_type: FuelType
    wfwx_station_uuid: str


class WeatherStation(BaseModel):
    """ A fire weather station has a code, planning area, and other properties specific to the station. """
    code: int
    station_props: WeatherStationProperties


class PlanningArea(BaseModel):
    """ A planning area (a.k.a. zone) is a small group of stations selected to represent a particular
    zone within a fire centre. """
    name: str
    order_of_appearance_in_list: Optional[int]
    stations: List[WeatherStation]


class FireCentre(BaseModel):
    """ The highest-level organizational unit for wildfire planning. Each fire centre
    has 1 or more planning areas within it. """
    id: int
    name: str
    planning_areas: List[PlanningArea]


class HFIWeatherStationsResponse(BaseModel):
    """ A list of WeatherStations, where each WeatherStation has nested within it all relevant information
    specific to BCWS planning operations. """
    fire_centres: List[FireCentre]


class HFIResultRequest(BaseModel):
    """
    Request that contains inputs necessary for calculating HFI
    """
    num_prep_days: int
    selected_prep_date: datetime
    # TODO: rename "time_stamp" to "date" - since we don't care about time.
    start_time_stamp: Optional[date]
    end_time_stamp: Optional[date]
    selected_station_codes: List[int]
    selected_fire_center: Optional[FireCentre]
    planning_area_fire_starts: Mapping[str, List[FireStartRange]]
    save: Optional[bool]


class HFIResultResponse(BaseModel):
    """
    Response that contains daily data, num prep days, selected station codes,
    selected fire centre, fire starts, HFI results
    """
    num_prep_days: int
    selected_prep_date: datetime
    start_time_stamp: Optional[date]
    end_time_stamp: Optional[date]
    selected_station_codes: List[int]
    selected_fire_center: Optional[FireCentre]
    planning_area_hfi_results: Mapping[str, PlanningAreaResult]
    planning_area_fire_starts: Mapping[str, List[FireStartRange]]
