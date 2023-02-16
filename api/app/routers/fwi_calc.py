""" Routers for FWI calculations. """
import logging
from datetime import timedelta
from typing import List
from fastapi import APIRouter, Depends
from aiohttp.client import ClientSession
from app.fwi.fwi import fwi_bui, fwi_ffmc, fwi_isi, fwi_fwi
from app.auth import audit, authentication_required
from app.utils.time import get_hour_20_from_date
from app.schemas.fwi_calc import (FWIIndices,
                                  FWIRequest,
                                  FWIOutput,
                                  FWIOutputResponse,
                                  Daily,
                                  MultiFWIInput,
                                  MultiFWIOutput,
                                  MultiFWIOutputResponse,
                                  MultiFWIRequest, YesterdayIndices)
from app.wildfire_one.wfwx_api import (get_auth_header,
                                       get_dailies,
                                       get_wfwx_stations_from_station_codes)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/fwi-calc",
    dependencies=[Depends(audit), Depends(authentication_required)],
)


async def dailies_list_mapper(raw_dailies):
    """ Maps raw stations to WeatherStation list"""
    dailies = []
    async for raw_daily in raw_dailies:
        dailies.append(
            Daily(
                temperature=raw_daily.get('temperature', None),
                status=raw_daily.get('recordType', '').get('id', None),
                relative_humidity=raw_daily.get('relativeHumidity', None),
                precipitation=raw_daily.get('precipitation', None),
                wind_direction=raw_daily.get('windDirection', None),
                ffmc=raw_daily.get('fineFuelMoistureCode', None),
                dmc=raw_daily.get('duffMoistureCode', None),
                dc=raw_daily.get('droughtCode', None),
                isi=raw_daily.get('initialSpreadIndex', None),
                bui=raw_daily.get('buildUpIndex', None),
                wind_speed=raw_daily.get('windSpeed', None)
            )
        )
    return dailies


async def calculate_actual(session: ClientSession, request, time_of_interest):
    """ Calculates actual FWI based on yesterday and today actuals """
    header = await get_auth_header(session)

    wfwx_stations = await get_wfwx_stations_from_station_codes(session, header, [request.input.stationCode])
    dailies_today: List[Daily] = await dailies_list_mapper(
        await get_dailies(session, header, wfwx_stations, time_of_interest))

    prev_day = time_of_interest - timedelta(days=1)
    dailies_yesterday: List[Daily] = await dailies_list_mapper(
        await get_dailies(session, header, wfwx_stations, prev_day))

    if len(dailies_today) == 0:
        return None, None

    ffmc = fwi_ffmc(
        dailies_yesterday[0].ffmc,
        dailies_today[0].temperature,
        dailies_today[0].relative_humidity,
        dailies_today[0].precipitation,
        dailies_today[0].wind_speed)
    isi = fwi_isi(ffmc, dailies_today[0].wind_speed)
    dmc = dailies_today[0].dmc
    dc = dailies_today[0].dc
    bui = fwi_bui(dailies_yesterday[0].dmc, dailies_yesterday[0].dc)
    fwi = fwi_fwi(isi, bui)
    yesterday_indices = YesterdayIndices(
        ffmc=dailies_yesterday[0].ffmc, dmc=dailies_yesterday[0].dmc, dc=dailies_yesterday[0].dc)
    indices = FWIIndices(
        ffmc=ffmc,
        dmc=dmc,
        dc=dc,
        isi=isi,
        bui=bui,
        fwi=fwi
    )
    return yesterday_indices, indices


async def calculate_adjusted(request: FWIRequest):
    """ Calculates adjusted FWI based on input and values """
    ffmc = fwi_ffmc(
        request.input.yesterdayFFMC,
        request.input.todayTemp,
        request.input.todayRH,
        request.input.todayPrecip,
        request.input.todayWindspeed)
    isi = fwi_isi(ffmc, request.input.todayWindspeed)
    dmc = request.input.yesterdayDMC
    dc = request.input.yesterdayDC
    bui = fwi_bui(dmc, dc)
    fwi = fwi_fwi(isi, bui)
    return FWIIndices(
        ffmc=ffmc,
        dmc=dmc,
        dc=dc,
        isi=isi,
        bui=bui,
        fwi=fwi
    )


@router.post('/', response_model=FWIOutputResponse)
async def get_fwi_calc_outputs(request: FWIRequest):
    """ Returns FWI calculations for all inputs """
    try:
        logger.info('/fwi_calc/')
        # we're interested in noon on the given day
        time_of_interest = get_hour_20_from_date(request.date)

        async with ClientSession() as session:
            yesterday_actual, actual = await calculate_actual(session, request, time_of_interest)
            adjusted = await calculate_adjusted(request)

            output = FWIOutput(
                datetime=get_hour_20_from_date(request.date),
                yesterday=yesterday_actual,
                actual=actual,
                adjusted=adjusted
            )

            return FWIOutputResponse(fwi_outputs=[output])
    except Exception as exception:
        logger.critical(exception, exc_info=True)
        raise


async def multi_calculate_actual(
        session: ClientSession,
        multi_fwi_input: MultiFWIInput,
        station_code: int,
        time_of_interest):
    """ Calculates actual FWI values based on date range """
    header = await get_auth_header(session)

    wfwx_stations = await get_wfwx_stations_from_station_codes(session, header, [station_code])
    dailies_today: List[Daily] = await dailies_list_mapper(
        await get_dailies(session, header, wfwx_stations, time_of_interest))

    prev_day = time_of_interest - timedelta(days=1)
    dailies_yesterday: List[Daily] = await dailies_list_mapper(
        await get_dailies(session, header, wfwx_stations, prev_day))

    if len(dailies_today) == 0 or len(dailies_yesterday) == 0:
        return FWIIndices(
            ffmc=0,
            dmc=0,
            dc=0,
            isi=0,
            bui=0,
            fwi=0
        )

    temp_input = multi_fwi_input.temp if multi_fwi_input.temp is not None else dailies_today[0].temperature
    rh_input = multi_fwi_input.rh if multi_fwi_input.rh is not None else dailies_today[0].relative_humidity
    precip_input = multi_fwi_input.precip if multi_fwi_input.precip is not None else dailies_today[
        0].precipitation
    wind_speed_input = multi_fwi_input.windSpeed if multi_fwi_input.windSpeed is not None else dailies_today[
        0].wind_speed

    is_adjusted = multi_fwi_input.temp is not None or \
        multi_fwi_input.rh is not None or \
        multi_fwi_input.precip is not None or \
        multi_fwi_input.windSpeed is not None

    status = 'ADJUSTED' if is_adjusted is True else dailies_today[0].status

    ffmc = fwi_ffmc(
        dailies_yesterday[0].ffmc,
        temp_input,
        rh_input,
        precip_input,
        wind_speed_input)
    isi = fwi_isi(ffmc, wind_speed_input)
    dmc = dailies_today[0].dmc
    dc = dailies_today[0].dc
    bui = fwi_bui(dailies_yesterday[0].dmc, dailies_yesterday[0].dc)
    fwi = fwi_fwi(isi, bui)
    output = MultiFWIOutput(id=multi_fwi_input.id,
                            datetime=multi_fwi_input.datetime,
                            status=status,
                            temp=temp_input,
                            rh=rh_input,
                            windDir=dailies_today[0].wind_direction,
                            windSpeed=wind_speed_input,
                            precip=precip_input,
                            actual=FWIIndices(
                                ffmc=ffmc,
                                dmc=dmc,
                                dc=dc,
                                isi=isi,
                                bui=bui,
                                fwi=fwi
                            ))
    return output


@router.post('/multi', response_model=MultiFWIOutputResponse)
async def get_multi_fwi_calc_outputs(request: MultiFWIRequest):
    """ Returns FWI calculations for all inputs """
    try:
        logger.info('/fwi_calc/multi')
        outputs: List[MultiFWIOutput] = []
        async with ClientSession() as session:

            for fwi_input in request.inputs:
                time_of_interest = get_hour_20_from_date(fwi_input.datetime)
                output: MultiFWIOutput = await multi_calculate_actual(
                    session, fwi_input, request.stationCode, time_of_interest)
                outputs.append(output)
            return MultiFWIOutputResponse(multi_fwi_outputs=outputs)
    except Exception as exception:
        logger.critical(exception, exc_info=True)
        raise
