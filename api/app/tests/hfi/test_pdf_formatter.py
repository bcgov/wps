import json
import os
from datetime import datetime
from typing import List
from jinja2 import Environment, FunctionLoader
from app.hfi.pdf_data_formatter import get_date_range_string, get_fire_start_labels, get_prep_levels, get_sorted_dates
from app.hfi.pdf_template import get_template
from app.schemas.hfi_calc import DailyResult, HFIResultResponse, StationDaily, lowest_fire_starts
from app.schemas.hfi_calc import FireCentre, HFIResultResponse

test_hfi_result = os.path.join(os.path.dirname(__file__), 'test_hfi_result.json')
test_fcs = os.path.join(os.path.dirname(__file__), 'test_fire_centres.json')
jinja_env = Environment(loader=FunctionLoader(get_template), autoescape=True)


def test_get_sorted_dates_all_unique():
    """ Unique dates are in sorted order """
    dailies: List[StationDaily] = [StationDaily(date=datetime.fromisocalendar(2022, 3, 3)),
                                   StationDaily(date=datetime.fromisocalendar(2022, 2, 2))]

    result = get_sorted_dates(dailies)
    assert result[0] == datetime.fromisocalendar(2022, 2, 2)
    assert result[1] == datetime.fromisocalendar(2022, 3, 3)


def test_get_sorted_dates_same():
    """ Only one date of each date is returned in order """
    dailies: List[StationDaily] = [StationDaily(date=datetime.fromisocalendar(2022, 3, 3)),
                                   StationDaily(date=datetime.fromisocalendar(2022, 3, 3)),
                                   StationDaily(date=datetime.fromisocalendar(2022, 3, 3)),
                                   StationDaily(date=datetime.fromisocalendar(2022, 3, 3))]

    result = get_sorted_dates(dailies)
    assert len(result) == 2
    assert result[0] == datetime.fromisocalendar(2022, 2, 2)
    assert result[1] == datetime.fromisocalendar(2022, 3, 3)


def test_get_date_range_string_2():
    """ Only one date of each date is returned in order """
    dates = [datetime.fromisocalendar(2022, 2, 2), datetime.fromisocalendar(2022, 3, 3)]
    result = get_date_range_string(dates)
    assert result == '2022-01-11 to 2022-01-19'


def test_get_date_range_string_3():
    """ Only one date of each date is returned in order """
    dates = [datetime.fromisocalendar(2022, 1, 1),
             datetime.fromisocalendar(2022, 2, 2),
             datetime.fromisocalendar(2022, 3, 3)]
    result = get_date_range_string(dates)
    assert result == '2022-01-03 to 2022-01-19'


def test_get_date_range_string_empty():
    """ Only one date of each date is returned in order """
    result = get_date_range_string([])
    assert result == ''


def test_get_date_range_string_single():
    """ Only one date of each date is returned in order """
    result = get_date_range_string([datetime.fromisocalendar(2022, 1, 1)])
    assert result == '2022-01-03'


def test_get_fire_start_labels():
    """ Returns the fire start labels from a planning area result """
    with open(test_hfi_result, 'r') as hfi_result:
        result_json = json.load(hfi_result)
        result = HFIResultResponse(**result_json)
        fire_labels = get_fire_start_labels(result, result.planning_area_hfi_results[0])
        assert fire_labels == ['0-1', '0-1', '0-1', '0-1', '0-1']


def test_get_prep_levels():
    """ Returns the prep levels from a list of daily results"""
    daily_results: List[DailyResult] = [
        DailyResult(
            date=datetime.fromisocalendar(2022, 2, 2),
            dailies=[],
            fire_starts=lowest_fire_starts,
            prep_level=1
        ),
        DailyResult(
            date=datetime.fromisocalendar(2022, 2, 2),
            dailies=[],
            fire_starts=lowest_fire_starts,
            prep_level=2
        )
    ]
    result = get_prep_levels(daily_results)
    assert result == [1, 2]
