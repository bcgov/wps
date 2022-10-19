import json
import os
from datetime import date, datetime, timedelta
from typing import List
from jinja2 import Environment, FunctionLoader
from app.hfi.pdf_data_formatter import (get_date_range_string,
                                        get_fire_start_labels,
                                        get_formatted_dates,
                                        get_mean_intensity_groups,
                                        get_merged_station_data,
                                        get_prep_levels,
                                        get_sorted_dates,
                                        response_2_daily_jinja_format,
                                        response_2_prep_cycle_jinja_format)
from app.hfi.pdf_generator import build_mappings
from app.hfi.pdf_template import get_template
from app.schemas.hfi_calc import (DailyResult, DateRange,
                                  FireCentre,
                                  HFIResultResponse,
                                  StationDaily, StationInfo,
                                  StationPDFData,
                                  WeatherStation,
                                  WeatherStationProperties,
                                  FireStartRange)
from app.schemas.hfi_calc import HFIResultResponse
from app.schemas.shared import FuelType

test_hfi_result = os.path.join(os.path.dirname(__file__), 'test_hfi_result.json')
test_fcs = os.path.join(os.path.dirname(__file__), 'test_fire_centres.json')
jinja_env = Environment(loader=FunctionLoader(get_template), autoescape=True)
lowest_fire_starts = (FireStartRange(id=1, label='0-1', ))


def test_get_sorted_dates_same():
    """ Only one date of each date is returned in order """
    start_date = date.fromisocalendar(2022, 2, 2)
    end_date = start_date + timedelta(days=6)
    date_range: DateRange = DateRange(start_date=start_date,
                                      end_date=end_date)

    result = get_sorted_dates(date_range)
    assert len(result) == 7
    assert result[0] == start_date
    assert result[6] == end_date


def test_get_date_range_string_2():
    """ Only one date of each date is returned in order """
    dates = [date.fromisocalendar(2022, 2, 2), date.fromisocalendar(2022, 3, 3)]
    result = get_date_range_string(dates)
    assert result == '2022-01-11 to 2022-01-19'


def test_get_date_range_string_3():
    """ Only one date of each date is returned in order """
    dates = [date.fromisocalendar(2022, 1, 1),
             date.fromisocalendar(2022, 2, 2),
             date.fromisocalendar(2022, 3, 3)]
    result = get_date_range_string(dates)
    assert result == '2022-01-03 to 2022-01-19'


def test_get_date_range_string_empty():
    """ Only one date of each date is returned in order """
    result = get_date_range_string([])
    assert result == ''


def test_get_date_range_string_single():
    """ Only one date of each date is returned in order """
    result = get_date_range_string([date.fromisocalendar(2022, 1, 1)])
    assert result == '2022-01-03'


def test_get_fire_start_labels():
    """ Returns the fire start labels from a planning area result """
    with open(test_hfi_result, 'r') as hfi_result:
        result_json = json.load(hfi_result)
        result = HFIResultResponse(**result_json)
        fire_labels = get_fire_start_labels(result.planning_area_hfi_results[0].daily_results)
        assert fire_labels == ['0-1', '0-1', '0-1']


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

        # dates test
        sorted_dates = get_sorted_dates(result.date_range)
        formatted_dates: List[str] = get_formatted_dates(sorted_dates)
        assert len(sorted_dates) == len(formatted_dates)

        for area_result in result.planning_area_hfi_results:
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
                                               elevation=1))
    weather_station_2 = WeatherStation(
        code=2,
        station_props=WeatherStationProperties(name='s2',
                                               wfwx_station_uuid='2',
                                               elevation=1,
                                               ))
    station_dict = {1: weather_station_1, 2: weather_station_2}
    station_daily1 = StationDaily(code=1, date=datetime.fromisocalendar(2022, 2, 2))
    station_daily2 = StationDaily(code=2, date=datetime.fromisocalendar(2022, 2, 2))
    fuel_types = {1: FuelType(id=1, abbrev='A', fuel_type_code='A', description='A')}
    planning_area_station_info = [StationInfo(station_code=1, selected=True, fuel_type_id=1),
                                  StationInfo(station_code=2, selected=True, fuel_type_id=1)]
    merged_station_data: List[StationPDFData] = get_merged_station_data(
        station_dict, [station_daily1, station_daily2], fuel_types, planning_area_station_info)
    assert len(merged_station_data) == 2
    assert merged_station_data[0].code == 1
    assert merged_station_data[0].station_props == weather_station_1.station_props
    assert merged_station_data[0].fuel_type == fuel_types[1]
    assert merged_station_data[1].code == 2
    assert merged_station_data[1].station_props == weather_station_2.station_props
    assert merged_station_data[1].fuel_type == fuel_types[1]


def test_response_2_prep_cycle_jinja_format():
    with open(test_hfi_result, 'r') as hfi_result, open(test_fcs, 'r') as fcs:
        result = json.load(hfi_result)
        fc_dict = json.load(fcs)
        fire_centres = []
        for fc_json in fc_dict['fire_centres']:
            fc = FireCentre(**fc_json)
            fire_centres.append(fc)

        fuel_types = {id: FuelType(id=id, abbrev='A', fuel_type_code='A', description='A')
                      for id in [22, 24, 26, 34]}
        _, planning_area_dict, station_dict = build_mappings(fire_centres)
        area_pdf_data, formatted_dates, date_range = response_2_prep_cycle_jinja_format(
            HFIResultResponse(**result), planning_area_dict, station_dict, fuel_types=fuel_types)

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
        assert formatted_dates == ['Monday August 02, 2021', 'Tuesday August 03, 2021',
                                   'Wednesday August 04, 2021']
        assert date_range == '2021-08-02 to 2021-08-04'


def test_response_2_daily_jinja_format():
    with open(test_hfi_result, 'r') as hfi_result, open(test_fcs, 'r') as fcs:
        result = json.load(hfi_result)
        fc_dict = json.load(fcs)
        fire_centres = []
        for fc_json in fc_dict['fire_centres']:
            fc = FireCentre(**fc_json)
            fire_centres.append(fc)

        _, planning_area_dict, station_dict = build_mappings(fire_centres)
        fuel_types = {id: FuelType(id=id, abbrev='A', fuel_type_code='A', description='A')
                      for id in [22, 24, 26, 34]}
        daily_pdf_data_by_date = response_2_daily_jinja_format(
            HFIResultResponse(**result), planning_area_dict, station_dict,
            fuel_types=fuel_types)

        # 4 daily results
        day_dates = list(daily_pdf_data_by_date.keys())
        assert len(day_dates) == 3
        assert day_dates[0] == '2021-08-02'
        assert day_dates[1] == '2021-08-03'
        assert day_dates[2] == '2021-08-04'

        for daily_planning_area_data in daily_pdf_data_by_date.values():
            # 7 planning areas in coastal
            assert len(daily_planning_area_data) == 7
            # assert correct order for each day
            for index in range(len(daily_planning_area_data)):
                assert daily_planning_area_data[index].order == index + 1
