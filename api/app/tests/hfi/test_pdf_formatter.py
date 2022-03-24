import json
import os
from datetime import datetime
from typing import List
from jinja2 import Environment, FunctionLoader
from app.hfi.pdf_data_formatter import (get_date_range_string,
                                        get_fire_start_labels,
                                        get_formatted_dates,
                                        get_mean_intensity_groups,
                                        get_merged_station_data,
                                        get_prep_levels,
                                        get_sorted_dates,
                                        get_station_dailies,
                                        response_2_daily_jinja_format,
                                        response_2_prep_cycle_jinja_format)
from app.hfi.pdf_generator import build_mappings
from app.hfi.pdf_template import get_template
from app.schemas.hfi_calc import (DailyResult,
                                  FireCentre,
                                  HFIResultResponse,
                                  StationDaily,
                                  StationPDFData,
                                  WeatherStation,
                                  WeatherStationProperties,
                                  lowest_fire_starts)
from app.schemas.hfi_calc import HFIResultResponse
from app.schemas.shared import FuelType

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
    dailies: List[StationDaily] = [StationDaily(date=datetime.fromisocalendar(2022, 2, 2)),
                                   StationDaily(date=datetime.fromisocalendar(2022, 2, 2)),
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


def test_get_mean_intensity_groups():
    """ Returns the prep levels from a list of daily results"""
    daily_results: List[DailyResult] = [
        DailyResult(
            date=datetime.fromisocalendar(2022, 2, 2),
            dailies=[],
            fire_starts=lowest_fire_starts,
            mean_intensity_group=1
        ),
        DailyResult(
            date=datetime.fromisocalendar(2022, 2, 2),
            dailies=[],
            fire_starts=lowest_fire_starts,
            mean_intensity_group=2
        )
    ]
    result = get_mean_intensity_groups(daily_results)
    assert result == [1, 2]


def test_all_array_functions():
    """ Per day metrics, ordered by date, shoud be the same length """
    with open(test_hfi_result, 'r') as hfi_result:
        result_json = json.load(hfi_result)
        result = HFIResultResponse(**result_json)

        for area_result in result.planning_area_hfi_results:
            area_dailies = get_station_dailies(area_result)

            # dates test
            sorted_dates = get_sorted_dates(area_dailies)
            formatted_dates: List[str] = get_formatted_dates(sorted_dates)
            assert len(sorted_dates) == len(formatted_dates)

            # # of migs and prep levels should equal # of dates
            mean_intensity_groups = get_mean_intensity_groups(area_result.daily_results)
            prep_levels = get_prep_levels(area_result.daily_results)

            assert len(sorted_dates) == len(mean_intensity_groups)
            assert len(formatted_dates) == len(mean_intensity_groups)
            assert len(sorted_dates) == len(prep_levels)
            assert len(formatted_dates) == len(prep_levels)


def test_get_merged_station_data():

    weather_station_1 = WeatherStation(
        code=1,
        station_props=WeatherStationProperties(name='s1',
                                               wfwx_station_uuid='1',
                                               elevation=1,
                                               fuel_type=FuelType(abbrev='f1',
                                                                  fuel_type_code='fc1',
                                                                  description='f1-desc')))
    weather_station_2 = WeatherStation(
        code=2,
        station_props=WeatherStationProperties(name='s2',
                                               wfwx_station_uuid='2',
                                               elevation=1,
                                               fuel_type=FuelType(abbrev='f2',
                                                                  fuel_type_code='fc2',
                                                                  description='f2-desc')))
    station_dict = {1: weather_station_1, 2: weather_station_2}
    station_daily1 = StationDaily(code=1, date=datetime.fromisocalendar(2022, 2, 2))
    station_daily2 = StationDaily(code=2, date=datetime.fromisocalendar(2022, 2, 2))
    merged_station_data: List[StationPDFData] = get_merged_station_data(
        station_dict, [station_daily1, station_daily2])
    assert len(merged_station_data) == 2
    assert merged_station_data[0].code == 1
    assert merged_station_data[0].station_props == weather_station_1.station_props
    assert merged_station_data[1].code == 2
    assert merged_station_data[1].station_props == weather_station_2.station_props


def test_response_2_prep_cycle_jinja_format():
    with open(test_hfi_result, 'r') as hfi_result, open(test_fcs, 'r') as fcs:
        result = json.load(hfi_result)
        fc_dict = json.load(fcs)
        fire_centres = []
        for fc_json in fc_dict['fire_centres']:
            fc = FireCentre(**fc_json)
            fire_centres.append(fc)

        _, planning_area_dict, station_dict = build_mappings(fire_centres)
        area_pdf_data, formatted_dates, date_range = response_2_prep_cycle_jinja_format(
            HFIResultResponse(**result), planning_area_dict, station_dict)

        # 7 planning areas in coastal
        assert len(area_pdf_data) == 7
        # assert correct order
        assert area_pdf_data[0].planning_area_name == 'Fraser Zone'
        assert area_pdf_data[1].planning_area_name == 'Pemberton Zone'
        assert area_pdf_data[2].planning_area_name == 'Sunshine Coast'
        assert area_pdf_data[3].planning_area_name == 'South Island'
        assert area_pdf_data[4].planning_area_name == 'Mid Island'
        assert area_pdf_data[5].planning_area_name == 'North Island'
        assert area_pdf_data[6].planning_area_name == 'Mid-Coast'
        assert formatted_dates == ['Monday August, 02, 2021', 'Tuesday August, 03, 2021',
                                   'Wednesday August, 04, 2021', 'Thursday August, 05, 2021']
        assert date_range == '2021-08-02 to 2021-08-05'


def test_response_2_daily_jinja_format():
    with open(test_hfi_result, 'r') as hfi_result, open(test_fcs, 'r') as fcs:
        result = json.load(hfi_result)
        fc_dict = json.load(fcs)
        fire_centres = []
        for fc_json in fc_dict['fire_centres']:
            fc = FireCentre(**fc_json)
            fire_centres.append(fc)

        _, planning_area_dict, station_dict = build_mappings(fire_centres)
        daily_pdf_data_by_date = response_2_daily_jinja_format(
            HFIResultResponse(**result), planning_area_dict, station_dict)

        # 4 daily results
        day_dates = list(daily_pdf_data_by_date.keys())
        assert len(day_dates) == 4
        assert day_dates[0] == '2021-08-02'
        assert day_dates[1] == '2021-08-03'
        assert day_dates[2] == '2021-08-04'
        assert day_dates[3] == '2021-08-05'

        for daily_planning_area_data in daily_pdf_data_by_date.values():
            # 7 planning areas in coastal
            assert len(daily_planning_area_data) == 7
            # assert correct order for each day
            assert daily_planning_area_data[0].planning_area_name == 'Fraser Zone'
            assert daily_planning_area_data[1].planning_area_name == 'Pemberton Zone'
            assert daily_planning_area_data[2].planning_area_name == 'Sunshine Coast'
            assert daily_planning_area_data[3].planning_area_name == 'South Island'
            assert daily_planning_area_data[4].planning_area_name == 'Mid Island'
            assert daily_planning_area_data[5].planning_area_name == 'North Island'
            assert daily_planning_area_data[6].planning_area_name == 'Mid-Coast'
