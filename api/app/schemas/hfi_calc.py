""" This module contains pydandict schemas the HFI Calculator.
"""
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
    date: date
    dailies: List[ValidatedStationDaily]
    fire_starts: FireStartRange
    mean_intensity_group: Optional[float]
    prep_level: Optional[float]


class PlanningAreaResult(BaseModel):
    """
    Mean prep level / max intensity group,
    dailies and validity status of station dailies in a planning area
    """
    planning_area_id: int
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
    order_of_appearance_in_planning_area_list: Optional[int]


class PlanningArea(BaseModel):
    """ A planning area (a.k.a. zone) is a small group of stations selected to represent a particular
    zone within a fire centre. """
    id: int
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


class StationInfo(BaseModel):
    """ Information about a station, including its code, name, and elevation. """
    station_code: int
    selected: bool
    # fuel_type_id matches to table fuel_types.id
    fuel_type_id: int


class HFILoadResultRequest(BaseModel):
    """ Request to load the HFI Calculator. """
    start_date: Optional[date]
    selected_fire_center_id: int


class HFIResultRequest(BaseModel):
    """
    Request that contains inputs necessary for calculating HFI.

    If a component on the front end needs a timestamp, then convert "2022-01-01" to a datetime at noon PST.
    Vice versa, if a component is working in terms of a timestamp, then convert from that timestamp to
    a ISO date string in PST, then grab the YYYY-MM-DD part.
    The PST part is critical, so that the date doesn't change due to timezone switches.
    """
    start_date: Optional[date]
    end_date: Optional[date]
    # TODO: Remove when fuel type config implemented
    selected_station_code_ids: List[int]
    # Each planning area has a list of stations
    planning_area_station_info: Optional[Mapping[int, List[StationInfo]]]
    selected_fire_center_id: int
    # Mapping from planning area id to a map of FireStartRanges.
    planning_area_fire_starts: Mapping[int, List[FireStartRange]]
    persist_request: Optional[bool]  # Indicate whether to save the request to the database.


class HFIResultResponse(BaseModel):
    """
    Response that contains daily data, num prep days, selected station codes,
    selected fire centre, fire starts, HFI results.
    """
    start_date: date
    end_date: date
    # TODO: Remove when fuel type config implemented
    selected_station_code_ids: List[int]
    planning_area_station_info: Optional[Mapping[int, List[StationInfo]]]
    selected_fire_center_id: int
    planning_area_hfi_results: List[PlanningAreaResult]
    # Mapping from planning area id to a map of FireStartRanges
    planning_area_fire_starts: Mapping[int, List[FireStartRange]]
    # Indicate whether the request used to generate this response  was saved to the database.
    request_persist_success: bool


class StationPDFData(StationDaily, WeatherStation):
    """ All the details we have about stations """


class PlanningAreaPDFData(BaseModel):
    """ Data needed for prep cycle PDF sheet """
    planning_area_name: str
    order: int
    mean_intensity_groups: List[float]
    fire_starts_labels: List[str]
    # Station dailies grouped by station code containing the dailies for each day in the prep cycle
    dailies: Mapping[int, List[StationPDFData]]


class PrepCyclePDFData(BaseModel):
    formatted_dates: List[str]
    planning_areas: List[PlanningAreaPDFData]


class DailyPDFData(BaseModel):
    """ Data needed for daily PDF sheet """
    planning_area_name: str
    highest_daily_intensity_group: Optional[float]
    mean_prep_level: Optional[float]
    fire_starts: str
    day: int
    days_total: int
    date: str
    # Every station daily in the above planning area for the specific day
    dailies: List[StationPDFData]
