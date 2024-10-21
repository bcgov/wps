from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Tuple
from osgeo import gdal, ogr, osr
import asyncio
import logging
import math
import numpy as np
import os
import requests
from sqlalchemy.ext.asyncio import AsyncSession
import statistics
import sys
import tempfile
import xml.etree.ElementTree as ET
from app import configure_logging
from app.db.crud.grass_curing import get_last_percent_grass_curing_for_date, save_percent_grass_curing
from app.db.database import get_async_read_session_scope, get_async_write_session_scope
from app.fire_behaviour import cffdrs
from app.fire_behaviour.fuel_types import FUEL_TYPE_DEFAULTS, FuelTypeEnum
from app.fire_behaviour.prediction import build_hourly_rh_dict, calculate_cfb, get_critical_hours
from app.fire_behaviour.wind_speed import calculate_wind_speed_result
from app.geospatial import WGS84
from app.db.models.grass_curing import PercentGrassCuring
from app.hourlies import get_hourly_readings_in_time_interval
from app.rocketchat_notifications import send_rocketchat_notification
from app.schemas.fba_calc import WindResult
from app.stations import get_stations_asynchronously


from aiohttp.client import ClientSession
from app.db.crud.auto_spatial_advisory import (
    get_all_sfms_fuel_type_records,
    get_fire_zone_unit_shape_type_id,
    get_most_recent_run_parameters,
    get_containing_zone,
    get_fuel_type_stats_in_advisory_area,
    save_critical_hours,
)
from app.db.models.auto_spatial_advisory import (
    AdvisoryFuelStats,
    CriticalHours,
    HfiClassificationThresholdEnum,
    Shape,
    ClassifiedHfi,
    HfiClassificationThreshold,
    SFMSFuelType,
    RunTypeEnum,
    FuelType,
    HighHfiArea,
    RunParameters,
    AdvisoryElevationStats,
    ShapeType,
)
from app.utils.time import get_hour_20_from_date, get_julian_date, get_utc_now
from app.wildfire_one import wfwx_api
from app.wildfire_one.schema_parsers import WFWXWeatherStation

logger = logging.getLogger(__name__)


class PointTransformer:
    def __init__(self, source_srs, target_srs):
        source = osr.SpatialReference()
        source.ImportFromEPSG(source_srs)
        target = osr.SpatialReference()
        target.ImportFromEPSG(target_srs)
        self.transform = osr.CoordinateTransformation(source, target)

    def transform_coordinate(self, x: float, y: float) -> Tuple[float, float]:
        point = ogr.CreateGeometryFromWkt(f"POINT ({x} {y})")
        point.Transform(self.transform)
        return (point.GetX(), point.GetY())


class CriticalHoursJob:
    def __init__(self):
        self.db_session = None
        self.client_session = None

    def _set_db_session(self, db_session: AsyncSession):
        self.db_session = db_session

    def _set_client_session(self, client_session: ClientSession):
        self.client_session = client_session

    def _calculate_wind_speed_result(self, yesterday: dict, raw_daily: dict) -> WindResult:
        # extract variable from wf1 that we need to calculate the fire behaviour advisory.
        bui = cffdrs.bui_calc(raw_daily.get("duffMoistureCode", None), raw_daily.get("droughtCode", None))
        temperature = raw_daily.get("temperature", None)
        relative_humidity = raw_daily.get("relativeHumidity", None)
        precipitation = raw_daily.get("precipitation", None)

        wind_speed = raw_daily.get("windSpeed", None)
        status = raw_daily.get("recordType").get("id")

        ffmc = cffdrs.fine_fuel_moisture_code(yesterday.get("fineFuelMoistureCode", None), temperature, relative_humidity, precipitation, wind_speed)
        isi = cffdrs.initial_spread_index(ffmc, wind_speed)
        fwi = cffdrs.fire_weather_index(isi, bui)
        return WindResult(ffmc=ffmc, isi=isi, bui=bui, wind_speed=wind_speed, fwi=fwi, status=status)

    async def _calculate_critical_hours():
        # Fetch all stations from WF1 API
        stations = get_stations_asynchronously()
        zone_unit_shape_type_id = await get_fire_zone_unit_shape_type_id()
        zone_units = 1
        stations_by_zone_unit = {}

    def _sort_station_by_zone(self, stations: list[WFWXWeatherStation]):
        stations_by_zone = defaultdict(list)
        for station in stations:
            stations_by_zone[station.zone_code].append(station)
        return stations_by_zone

    async def _get_most_recent_sfms_run_parameters(self, run_type: RunTypeEnum, for_date: datetime):
        result = await get_most_recent_run_parameters(self.db_session, RunTypeEnum.forecast, date(2024, 7, 16))
        if len(result) > 0:
            return result[0]
        return None

    # def _get_high_hfi_fuel_types(self, session: ClientSession, station_code: int, for_date: datetime):

    async def _calculate_critical_hours_for_station_by_fuel_type(
        self,
        wfwx_station: WFWXWeatherStation,
        dailies_by_station_id: dict,
        yesterday_dailies_by_station_id: dict,
        hourly_observations_by_station_id: dict,
        fuel_type: FuelTypeEnum,
        for_date: datetime,
    ):
        raw_daily = dailies_by_station_id[wfwx_station.wfwx_id]
        raw_observations = hourly_observations_by_station_id[wfwx_station.code]
        yesterday = yesterday_dailies_by_station_id[wfwx_station.wfwx_id]
        last_observed_morning_rh_values = build_hourly_rh_dict(raw_observations.values)

        wind_result = self._calculate_wind_speed_result(yesterday, raw_daily)
        bui = wind_result.bui
        ffmc = wind_result.ffmc
        isi = wind_result.isi
        fuel_type_info = FUEL_TYPE_DEFAULTS[fuel_type]
        percentage_conifer = fuel_type_info.get("PC", None)
        percentage_dead_balsam_fir = fuel_type_info.get("PDF", None)
        crown_base_height = fuel_type_info.get("CBH", None)
        cfl = fuel_type_info.get("CFL", None)
        grass_cure = yesterday.get("grasslandCuring", None)
        wind_speed = wind_result.wind_speed
        yesterday_ffmc = yesterday.get("fineFuelMoistureCode", None)
        julian_date = get_julian_date(for_date)
        fmc = cffdrs.foliar_moisture_content(int(wfwx_station.lat), int(wfwx_station.long), wfwx_station.elevation, julian_date)
        sfc = cffdrs.surface_fuel_consumption(fuel_type, bui, ffmc, percentage_conifer)
        ros = cffdrs.rate_of_spread(
            fuel_type,
            isi=isi,
            bui=bui,
            fmc=fmc,
            sfc=sfc,
            pc=percentage_conifer,
            cc=grass_cure,
            pdf=percentage_dead_balsam_fir,
            cbh=crown_base_height,
        )
        cfb = calculate_cfb(fuel_type, fmc, sfc, ros, crown_base_height)

        critical_hours = get_critical_hours(
            4000,
            fuel_type,
            percentage_conifer,
            percentage_dead_balsam_fir,
            bui,
            grass_cure,
            crown_base_height,
            ffmc,
            fmc,
            cfb,
            cfl,
            wind_speed,
            yesterday_ffmc,
            last_observed_morning_rh_values,
        )

        return critical_hours

    # async def _calculate_critical_hours_for_stations(self, header, stations):
    #     for_date = get_hour_20_from_date(get_utc_now())
    #     time_of_interest = get_hour_20_from_date(for_date)
    #     unique_station_codes = list(set(station.code for station in stations))
    #     # get the dailies for all the stations
    #     dailies = await wfwx_api.get_dailies_generator(self.session, header, stations, time_of_interest, time_of_interest)
    #     # turn it into a dictionary so we can easily get at data using a station id
    #     dailies_by_station_id = {raw_daily.get("stationId"): raw_daily async for raw_daily in dailies}
    #     # must retrieve the previous day's observed/forecasted FFMC value from WFWX
    #     prev_day = time_of_interest - timedelta(days=1)
    #     # get the "daily" data for the station for the previous day
    #     yesterday_response = await wfwx_api.get_dailies_generator(self.session, header, stations, prev_day, prev_day)
    #     # turn it into a dictionary so we can easily get at data
    #     yesterday_dailies_by_station_id = {raw_daily.get("stationId"): raw_daily async for raw_daily in yesterday_response}
    #     # get hourly observation history from our API (used for calculating morning diurnal FFMC)
    #     hourly_observations = await get_hourly_readings_in_time_interval(unique_station_codes, time_of_interest - timedelta(days=4), time_of_interest)
    #     # also turn hourly obs data into a dict indexed by station id
    #     hourly_obs_by_station_code = {raw_hourly.station.code: raw_hourly for raw_hourly in hourly_observations}

    #     # we need a lookup from station code to station id
    #     # TODO: this is a bit silly, the call to get_wfwx_stations_from_station_codes repeats a lot of this!
    #     wfwx_station_lookup = {wfwx_station.code: wfwx_station for wfwx_station in stations}
    #     stations_critical_hours = {}
    #     for station in stations:
    #         critical_hours = await self._calculate_critical_hours_for_station(station, dailies_by_station_id, yesterday_dailies_by_station_id, hourly_obs_by_station_code, for_date)
    #         return

    def _get_fuel_types_by_area(self, advisory_fuel_stats):
        fuel_types_by_area = {}
        for row in advisory_fuel_stats:
            advisory_fuel_stat = row[0]
            sfms_fuel_type = row[1]
            key = sfms_fuel_type.fuel_type_code
            if key == "Non-fuel":
                continue
            if key in fuel_types_by_area:
                fuel_types_by_area[key] += advisory_fuel_stat.area
            else:
                fuel_types_by_area[key] = advisory_fuel_stat.area
        return fuel_types_by_area

    def _calculate_representative_hours(self, critical_hours):
        print(critical_hours)

    def _check_station_valid(self, wfwx_station: WFWXWeatherStation, dailies, hourlies) -> bool:
        """
        Checks if there is sufficient information to calculate critical hours for the specified station.

        :param wfwx_station: The station of interest.
        :param yesterdays: Yesterday's station data based on observations and FWI calculations.
        :param hourlies: Hourly observations from yesterday.
        :return: True if the station can be used for critical hours calculations, otherwise false.
        """
        if wfwx_station.wfwx_id not in dailies or wfwx_station.code not in hourlies:
            return False
        daily = dailies[wfwx_station.wfwx_id]
        if daily["duffMoistureCode"] is None or daily["droughtCode"] is None or daily["fineFuelMoistureCode"] is None:
            return False
        return True

    def _determine_start_time(self, times: list[float]) -> float:
        if len(times) < 3:
            return min(times)
        return math.floor(np.percentile(times, 25))

    def _determine_end_time(self, times: list[float]) -> float:
        if len(times) < 3:
            return max(times)
        return math.ceil(np.percentile(times, 75))

    def _calculate_representative_hours(self, critical_hours):
        start_times = []
        end_times = []
        for hours in critical_hours:
            start_times.append(hours.start)
            end_times.append(hours.end)
        start_time = self._determine_start_time(start_times)
        end_time = self._determine_end_time(end_times)
        return (start_time, end_time)

    async def _get_sfms_fuel_types_dict(self):
        sfms_fuel_types = await get_all_sfms_fuel_type_records(self.db_session)
        fuel_types_dict = defaultdict()
        for fuel_type in sfms_fuel_types:
            fuel_types_dict[fuel_type[0].fuel_type_code] = fuel_type[0].id
        return fuel_types_dict

    async def _save_critical_hours(self, zone_id: int, critical_hours_by_fuel_type: dict, run_parameters_id: int):
        sfms_fuel_types_dict = await self._get_sfms_fuel_types_dict()
        critical_hours_to_save: list[CriticalHours] = []
        for fuel_type, critical_hours in critical_hours_by_fuel_type.items():
            start_time, end_time = self._calculate_representative_hours(critical_hours)
            critical_hours_record = CriticalHours(
                advisory_shape_id=zone_id,
                threshold=HfiClassificationThresholdEnum.ADVISORY.value,
                run_parameters=run_parameters_id,
                fuel_type=sfms_fuel_types_dict[fuel_type],
                start_hour=start_time,
                end_hour=end_time,
            )
            critical_hours_to_save.append(critical_hours_record)
        await save_critical_hours(self.db_session, critical_hours_to_save)
        print(fuel_type)

    async def _calculate_critical_hours_by_zone(self, header, stations_by_zone):
        for_date = get_hour_20_from_date(get_utc_now())
        time_of_interest = get_hour_20_from_date(for_date)
        run_parameters = await self._get_most_recent_sfms_run_parameters(RunTypeEnum.forecast, date(2024, 8, 7))
        run_parameters_id = run_parameters.id
        critical_hours_by_zone_and_fuel_type = defaultdict(str, defaultdict(list))
        for zone_key in stations_by_zone.keys():
            critical_hours_by_station = defaultdict(list)
            advisory_fuel_stats = await get_fuel_type_stats_in_advisory_area(self.db_session, zone_key, run_parameters_id)
            fuel_types_by_area = self._get_fuel_types_by_area(advisory_fuel_stats)
            wfwx_stations = stations_by_zone[zone_key]
            unique_station_codes = list(set(station.code for station in wfwx_stations))
            # get the dailies for all the stations
            async with ClientSession() as client_session:
                dailies = await wfwx_api.get_dailies_generator(client_session, header, wfwx_stations, time_of_interest, time_of_interest)
                # turn it into a dictionary so we can easily get at data using a station id
                dailies_by_station_id = {raw_daily.get("stationId"): raw_daily async for raw_daily in dailies}
                # must retrieve the previous day's observed/forecasted FFMC value from WFWX
                prev_day = time_of_interest - timedelta(days=1)
                # get the "daily" data for the station for the previous day
                yesterday_response = await wfwx_api.get_dailies_generator(client_session, header, wfwx_stations, prev_day, prev_day)
                # turn it into a dictionary so we can easily get at data
                yesterday_dailies_by_station_id = {raw_daily.get("stationId"): raw_daily async for raw_daily in yesterday_response}
                # get hourly observation history from our API (used for calculating morning diurnal FFMC)
                hourly_observations = await get_hourly_readings_in_time_interval(unique_station_codes, time_of_interest - timedelta(days=4), time_of_interest)
                # also turn hourly obs data into a dict indexed by station id
                hourly_obs_by_station_code = {raw_hourly.station.code: raw_hourly for raw_hourly in hourly_observations}

                # we need a lookup from station code to station id
                # TODO: this is a bit silly, the call to get_wfwx_stations_from_station_codes repeats a lot of this!
                wfwx_station_lookup = {wfwx_station.code: wfwx_station for wfwx_station in wfwx_stations}

            for wfwx_station in wfwx_stations:
                if self._check_station_valid(wfwx_station, dailies_by_station_id, hourly_obs_by_station_code):
                    for fuel_type_key in fuel_types_by_area.keys():
                        fuel_type_enum = FuelTypeEnum(fuel_type_key.replace("-", ""))
                        try:
                            # Placing critical hours calculation in a try/except block as failure to calculate critical hours for a single station/fuel type pair
                            # shouldn't prevent us from continuing with other stations and fuel types.
                            critical_hours = await self._calculate_critical_hours_for_station_by_fuel_type(
                                wfwx_station, dailies_by_station_id, yesterday_dailies_by_station_id, hourly_obs_by_station_code, fuel_type_enum, for_date
                            )
                            if critical_hours is not None and critical_hours.start is not None and critical_hours.end is not None:
                                critical_hours_by_station[fuel_type_key].append(critical_hours)
                        except Exception as exc:
                            logger.warning(f"An error occurred when calculating critical hours for station code: {wfwx_station.code} and fuel type: {fuel_type_key}: {exc} ")
            if len(critical_hours_by_station) > 0:
                critical_hours_by_zone_and_fuel_type[zone_key] = critical_hours_by_station

        for zone_id, critical_hours_by_fuel_type in critical_hours_by_zone_and_fuel_type.items():
            await self._save_critical_hours(zone_id, critical_hours_by_fuel_type, run_parameters_id)
            print(zone_id)

        return critical_hours_by_zone_and_fuel_type

    async def _sort_stations_by_zone_unit(self, stations):
        stations_by_zone = defaultdict(list)
        transformer = PointTransformer(4326, 3005)
        for station in stations:
            (x, y) = transformer.transform_coordinate(station.lat, station.long)
            zone_id = await get_containing_zone(self.db_session, f"POINT({x} {y})", 3005)
            if zone_id is not None:
                stations_by_zone[zone_id[0]].append(station)
        return stations_by_zone

    async def _run_critical_hours(self):
        """Entry point for running the job."""
        # Somehow check the last time critical hours were calculated
        async with ClientSession() as client_session:
            header = await wfwx_api.get_auth_header(client_session)
            all_stations = await get_stations_asynchronously()
            station_codes = list(station.code for station in all_stations)
            stations = await wfwx_api.get_wfwx_stations_from_station_codes(client_session, header, station_codes)
            stations_by_zone = await self._sort_stations_by_zone_unit(stations)

        critical_hours_by_zone = await self._calculate_critical_hours_by_zone(header, stations_by_zone)

        print("test")
        # await self._calculate_critical_hours()

    async def run_job(self):
        # Create a db session and client session for use throughout the job.
        async with get_async_write_session_scope() as db_session:
            self._set_db_session(db_session)
            async with ClientSession() as client_session:
                self._set_client_session(client_session)
                await self._run_critical_hours()


def main():
    """Kicks off asynchronous calculation of critical hours."""
    try:
        logger.debug("Begin calculating critical hours.")

        job = CriticalHoursJob()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(job.run_job())

        # Exit with 0 - success.
        sys.exit(os.EX_OK)
    except Exception as exception:
        # Exit non 0 - failure.
        logger.error("An error occurred while processing critical hours.", exc_info=exception)
        rc_message = ":scream: Encountered an error while processing critical hours."
        send_rocketchat_notification(rc_message, exception)
        sys.exit(os.EX_SOFTWARE)


if __name__ == "__main__":
    configure_logging()
    main()