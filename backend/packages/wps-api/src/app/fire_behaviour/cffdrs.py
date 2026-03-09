"""This module contains functions for computing fire weather metrics."""

import logging
import math
from typing import Optional

import pandas as pd
from cffdrs import (
    buildup_index,
)
from cffdrs import (
    drought_code as _drought_code,
)
from cffdrs import (
    duff_moisture_code as _duff_moisture_code,
)
from cffdrs import (
    fine_fuel_moisture_code as _fine_fuel_moisture_code,
)
from cffdrs import (
    fire_weather_index as _fire_weather_index,
)
from cffdrs import (
    initial_spread_index as _initial_spread_index,
)
from cffdrs.back_rate_of_spread import back_rate_of_spread as _back_rate_of_spread
from cffdrs.cfb_calc import critical_surface_intensity, surface_fire_rate_of_spread
from cffdrs.cfb_calc import crown_fraction_burned as _crown_fraction_burned
from cffdrs.distance_at_time import distance_at_time
from cffdrs.fire_intensity import fire_intensity
from cffdrs.flank_rate_of_spread import flank_rate_of_spread as _flank_rate_of_spread
from cffdrs.foliar_moisture_content import foliar_moisture_content as _foliar_moisture_content
from cffdrs.hourly_fine_fuel_moisture_code import hourly_fine_fuel_moisture_code as _hourly_ffmc
from cffdrs.length_to_breadth import length_to_breadth
from cffdrs.length_to_breadth_at_time import length_to_breadth_at_time
from cffdrs.rate_of_spread import rate_of_spread as _rate_of_spread
from cffdrs.rate_of_spread_at_time import rate_of_spread_at_time
from cffdrs.slope_calc import slope_adjustment
from cffdrs.surface_fuel_consumption import surface_fuel_consumption as _surface_fuel_consumption
from cffdrs.total_fuel_consumption import total_fuel_consumption as _total_fuel_consumption
from wps_shared.fuel_types import FuelTypeEnum

logger = logging.getLogger(__name__)


# Computable: SFC, FMC
# To store in DB: PC, PDF, CC, CBH (attached to fuel type, red book)
PARAMS_ERROR_MESSAGE = "One or more params passed to cffdrs call is None."

# Fuel types that require specific optional parameters.
_FUEL_TYPES_REQUIRING_PC = {FuelTypeEnum.M1, FuelTypeEnum.M2}
_FUEL_TYPES_REQUIRING_PDF = {FuelTypeEnum.M3, FuelTypeEnum.M4}
_FUEL_TYPES_REQUIRING_CC = {FuelTypeEnum.O1A, FuelTypeEnum.O1B}


class CFFDRSException(Exception):
    """CFFDRS contextual exception"""


def _validate_fuel_type_params(
    fuel_type: FuelTypeEnum, pc: float, pdf: float, cc: float, cbh: float
):
    """Raise CFFDRSException if a parameter required for the given fuel type is None.

    pc, pdf, and cc are only required for the fuel types that use them.
    cbh is always required because cffdrs_py unconditionally computes critical surface intensity.
    Callers should resolve cbh from FUEL_TYPE_DEFAULTS before calling cffdrs functions.
    """
    if cbh is None:
        raise CFFDRSException(
            f"cbh is required for fuel_type {fuel_type.value}; pass crown_base_height or use FUEL_TYPE_DEFAULTS"
        )
    if fuel_type in _FUEL_TYPES_REQUIRING_PC and pc is None:
        raise CFFDRSException(f"pc is required for fuel_type {fuel_type.value}")
    if fuel_type in _FUEL_TYPES_REQUIRING_PDF and pdf is None:
        raise CFFDRSException(f"pdf is required for fuel_type {fuel_type.value}")
    if fuel_type in _FUEL_TYPES_REQUIRING_CC and cc is None:
        raise CFFDRSException(f"cc is required for fuel_type {fuel_type.value}")


def correct_wind_azimuth(wind_direction: float):
    """
    Corrections to reorient Wind Azimuth (WAZ).
    WAZ = WD + pi; if WAZ > 2*pi: WAZ -= 2*pi
    """
    if wind_direction is None:
        return None
    waz = wind_direction + math.pi
    if waz > 2 * math.pi:
        return waz - 2 * math.pi
    return waz


def calculate_wind_speed(
    fuel_type: FuelTypeEnum,
    ffmc: float,
    bui: float,
    ws: float,
    fmc: float,
    sfc: float,
    pc: float,
    cc: float,
    pdf: float,
    cbh: float,
    isi: float,
):
    """
    Wind azimuth, slope azimuth, ground slope, net effective windspeed
    """
    wind_azimuth = correct_wind_azimuth(ws)
    slope_azimuth = None  # a.k.a. SAZ
    ground_slope = 0  # right now we're not taking slope into account
    wsv = calculate_net_effective_windspeed(
        fuel_type=fuel_type,
        ffmc=ffmc,
        bui=bui,
        ws=ws,
        waz=wind_azimuth,
        gs=ground_slope,
        saz=slope_azimuth,
        fmc=fmc,
        sfc=sfc,
        pc=pc,
        cc=cc,
        pdf=pdf,
        cbh=cbh,
        isi=isi,
    )
    return wsv


def calculate_net_effective_windspeed(
    fuel_type: FuelTypeEnum,
    ffmc: float,
    bui: float,
    ws: float,
    waz: float,
    gs: float,
    saz: Optional[float],
    fmc: float,
    sfc: float,
    pc: float,
    cc: float,
    pdf: float,
    cbh: float,
    isi: float,
):
    """
    Calculate the net effective windspeed (WSV).
    """
    if gs > 0 and ffmc > 0:
        _validate_fuel_type_params(fuel_type, pc, pdf, cc, cbh)
        result = slope_adjustment(
            fuel_type=fuel_type.value,
            ffmc=ffmc,
            bui=bui,
            ws=ws,
            waz=waz,
            gs=gs,
            saz=saz,
            fmc=fmc,
            sfc=sfc,
            pc=pc,
            pdf=pdf,
            cc=cc,
            cbh=cbh,
            isi=isi,
        )
        return result.wsv
    return ws


def flank_rate_of_spread(ros: float, bros: float, lb: float):
    """Calculate the Flank Fire Spread Rate."""
    return _flank_rate_of_spread(ros, bros, lb)


def back_rate_of_spread(
    fuel_type: FuelTypeEnum,
    ffmc: float,
    bui: float,
    wsv: float,
    fmc: float,
    sfc: float,
    pc: float,
    cc: float,
    pdf: float,
    cbh: float,
):
    """Calculate the Back Fire Spread Rate."""
    if fuel_type is None or ffmc is None or bui is None or fmc is None or sfc is None:
        message = (
            PARAMS_ERROR_MESSAGE
            + f"_BROScalc ; fuel_type: {fuel_type.value}, ffmc: {ffmc}, bui: {bui}, fmc: {fmc}, sfc: {sfc}"
        )
        raise CFFDRSException(message)
    _validate_fuel_type_params(fuel_type, pc, pdf, cc, cbh)

    return _back_rate_of_spread(
        fuel_type=fuel_type.value,
        ffmc=ffmc,
        bui=bui,
        wsv=wsv if wsv is not None else 0,
        fmc=fmc,
        sfc=sfc,
        pc=pc,
        pdf=pdf,
        cc=cc,
        cbh=cbh,
    )


def bui_calc(dmc: float, dc: float):
    """Buildup Index calculation."""
    if dmc is None or dc is None:
        return None
    return buildup_index(dmc, dc)


def rate_of_spread_t(
    fuel_type: FuelTypeEnum, ros_eq: float, minutes_since_ignition: float, cfb: float
):
    """
    Computes the Rate of Spread prediction at elapsed time since ignition.
    NOTE: HR is minutes since ignition (not hours, despite the documentation).
    """
    return rate_of_spread_at_time(fuel_type.value, ros_eq, minutes_since_ignition, cfb)


def rate_of_spread(
    fuel_type: FuelTypeEnum,
    isi: float,
    bui: float,
    fmc: float,
    sfc: float,
    pc: float,
    cc: float,
    pdf: float,
    cbh: float,
):
    """Computes Rate of Spread (m/min)."""
    if fuel_type is None or isi is None or bui is None or sfc is None:
        message = (
            PARAMS_ERROR_MESSAGE
            + f"_ROScalc ; fuel_type: {fuel_type.value}, isi: {isi}, bui: {bui}, fmc: {fmc}, sfc: {sfc}"
        )
        raise CFFDRSException(message)
    _validate_fuel_type_params(fuel_type, pc, pdf, cc, cbh)

    return _rate_of_spread(
        fuel_type=fuel_type.value,
        isi=isi,
        bui=bui,
        fmc=fmc,
        sfc=sfc,
        pc=pc,
        pdf=pdf,
        cc=cc,
        cbh=cbh,
    )


def surface_fuel_consumption(fuel_type: FuelTypeEnum, bui: float, ffmc: float, pc: float):
    """Computes SFC. Assumes a standard GFL of 0.35 kg/m^2."""
    if fuel_type is None or bui is None or ffmc is None:
        message = (
            PARAMS_ERROR_MESSAGE
            + f"_SFCcalc; fuel_type: {fuel_type.value}, bui: {bui}, ffmc: {ffmc}"
        )
        raise CFFDRSException(message)
    if fuel_type in _FUEL_TYPES_REQUIRING_PC and pc is None:
        raise CFFDRSException(f"pc is required for fuel_type {fuel_type.value}")

    # Note: cffdrs_py signature is (fuel_type, ffmc, bui, pc, gfl) — ffmc before bui
    return _surface_fuel_consumption(
        fuel_type=fuel_type.value,
        ffmc=ffmc,
        bui=bui,
        pc=pc,
        gfl=0.35,
    )


def fire_distance(fuel_type: FuelTypeEnum, ros_eq: float, hr: int, cfb: float):
    """Calculate the Head fire spread distance at time t."""
    return distance_at_time(fuel_type.value, ros_eq, hr, cfb)


def foliar_moisture_content(
    lat: int,
    long: int,
    elv: float,
    day_of_year: int,
    date_of_minimum_foliar_moisture_content: int = 0,
):
    """Computes FMC."""
    logger.debug(
        "calling FMCcalc(LAT=%s, LONG=%s, ELV=%s, DJ=%s, D0=%s)",
        lat,
        long,
        elv,
        day_of_year,
        date_of_minimum_foliar_moisture_content,
    )
    # FMCcalc expects longitude to always be a positive number.
    if long < 0:
        long = -long
    return _foliar_moisture_content(
        lat=lat, long=long, elv=elv, dj=day_of_year, d0=date_of_minimum_foliar_moisture_content
    )


def length_to_breadth_ratio(fuel_type: FuelTypeEnum, wind_speed: float):
    """Computes L/B ratio."""
    if wind_speed is None or fuel_type is None:
        raise CFFDRSException(
            PARAMS_ERROR_MESSAGE
            + f"length_to_breadth_ratio; fuel_type: {fuel_type}, wind_speed: {wind_speed}"
        )
    return length_to_breadth(fuel_type.value, wind_speed)


def length_to_breadth_ratio_t(
    fuel_type: FuelTypeEnum, lb: float, time_since_ignition: float, cfb: float
):
    """Computes L/B ratio at elapsed time since ignition."""
    return length_to_breadth_at_time(fuel_type.value, lb, time_since_ignition, cfb)


def fine_fuel_moisture_code(
    ffmc: float,
    temperature: float,
    relative_humidity: float,
    precipitation: float,
    wind_speed: float,
):
    """Computes Fine Fuel Moisture Code (FFMC)."""
    if ffmc is None:
        logger.error("Failed to calculate FFMC; initial FFMC is required.")
        return None
    if wind_speed is None:
        logger.error("Failed to calculate ffmc")
        return None
    if temperature is None or relative_humidity is None or precipitation is None:
        return None
    return _fine_fuel_moisture_code(
        ffmc_yda=ffmc, temp=temperature, rh=relative_humidity, ws=wind_speed, prec=precipitation
    )


def duff_moisture_code(
    dmc: float,
    temperature: float,
    relative_humidity: float,
    precipitation: float,
    latitude: float = 55,
    month: int = 7,
    latitude_adjust: bool = True,
):
    """Computes Duff Moisture Code (DMC)."""
    if dmc is None:
        logger.error("Failed to calculate DMC; initial DMC is required.")
        return None
    if temperature is None or relative_humidity is None or precipitation is None:
        return None
    if latitude is None:
        latitude = 55
    if month is None:
        month = 7
    return _duff_moisture_code(
        dmc_yda=dmc,
        temp=temperature,
        rh=relative_humidity,
        prec=precipitation,
        lat=latitude,
        mon=month,
        lat_adjust=latitude_adjust,
    )


def drought_code(
    dc: float,
    temperature: float,
    relative_humidity: float,
    precipitation: float,
    latitude: float = 55,
    month: int = 7,
    latitude_adjust: bool = True,
):
    """Computes Drought Code (DC)."""
    if dc is None:
        logger.error("Failed to calculate DC; initial DC is required.")
        return None
    if temperature is None or relative_humidity is None or precipitation is None:
        return None
    if latitude is None:
        latitude = 55
    if month is None:
        month = 7
    return _drought_code(
        dc_yda=dc,
        temp=temperature,
        rh=relative_humidity,
        prec=precipitation,
        lat=latitude,
        mon=month,
        lat_adjust=latitude_adjust,
    )


def initial_spread_index(ffmc: float, wind_speed: float, fbp_mod: bool = False):
    """Computes Initial Spread Index (ISI)."""
    if ffmc is None or wind_speed is None:
        return None
    return _initial_spread_index(ffmc=ffmc, ws=wind_speed, fbp_mod=fbp_mod)


def fire_weather_index(isi: float, bui: float):
    """Computes Fire Weather Index (FWI)."""
    if isi is None or bui is None:
        return None
    return _fire_weather_index(isi=isi, bui=bui)


def crown_fraction_burned(
    fuel_type: FuelTypeEnum, fmc: float, sfc: float, ros: float, cbh: float
) -> float:
    """Computes Crown Fraction Burned (CFB). Value returned will be between 0-1."""
    if cbh is None or fmc is None or sfc is None or ros is None:
        message = (
            PARAMS_ERROR_MESSAGE
            + f"_CFBcalc; fuel_type: {fuel_type.value}, cbh: {cbh}, fmc: {fmc}, sfc: {sfc}, ros: {ros}"
        )
        raise CFFDRSException(message)
    csi = critical_surface_intensity(fmc, cbh)
    rso = surface_fire_rate_of_spread(csi, sfc)
    return _crown_fraction_burned(ros, rso)


def total_fuel_consumption(
    fuel_type: FuelTypeEnum, cfb: float, sfc: float, pc: float, pdf: float, cfl: float
):
    """Computes Total Fuel Consumption (TFC)."""
    if cfb is None or cfl is None:
        message = (
            PARAMS_ERROR_MESSAGE + f"_TFCcalc; fuel_type: {fuel_type.value}, cfb: {cfb}, cfl: {cfl}"
        )
        raise CFFDRSException(message)
    if fuel_type in _FUEL_TYPES_REQUIRING_PC and pc is None:
        raise CFFDRSException(f"pc is required for fuel_type {fuel_type.value}")
    if fuel_type in _FUEL_TYPES_REQUIRING_PDF and pdf is None:
        raise CFFDRSException(f"pdf is required for fuel_type {fuel_type.value}")
    return _total_fuel_consumption(
        fuel_type=fuel_type.value,
        cfl=cfl,
        cfb=cfb,
        sfc=sfc,
        pc=pc,
        pdf=pdf,
    )


def head_fire_intensity(
    fuel_type: FuelTypeEnum,
    percentage_conifer: float,
    percentage_dead_balsam_fir: float,
    ros: float,
    cfb: float,
    cfl: float,
    sfc: float,
):
    """Computes Head Fire Intensity (HFI)."""
    tfc = total_fuel_consumption(
        fuel_type, cfb, sfc, percentage_conifer, percentage_dead_balsam_fir, cfl
    )
    return fire_intensity(fc=tfc, ros=ros)


def get_ffmc_for_target_hfi(
    fuel_type: FuelTypeEnum,
    percentage_conifer: float,
    percentage_dead_balsam_fir: float,
    bui: float,
    wind_speed: float,
    grass_cure: int,
    crown_base_height: float,
    ffmc: float,
    fmc: float,
    cfb: float,
    cfl: float,
    target_hfi: float,
):
    """Returns a floating point value for minimum FFMC required (holding all other values constant)
    before HFI reaches the target_hfi (in kW/m).
    """
    # start off using the actual FFMC value
    experimental_ffmc = ffmc
    experimental_sfc = surface_fuel_consumption(
        fuel_type, bui, experimental_ffmc, percentage_conifer
    )
    experimental_isi = initial_spread_index(experimental_ffmc, wind_speed)
    experimental_ros = rate_of_spread(
        fuel_type,
        experimental_isi,
        bui,
        fmc,
        experimental_sfc,
        percentage_conifer,
        grass_cure,
        percentage_dead_balsam_fir,
        crown_base_height,
    )
    experimental_hfi = head_fire_intensity(
        fuel_type,
        percentage_conifer,
        percentage_dead_balsam_fir,
        experimental_ros,
        cfb,
        cfl,
        experimental_sfc,
    )
    error_hfi = (target_hfi - experimental_hfi) / target_hfi

    # FFMC has upper bound 101
    # exit condition 1: FFMC of 101 still causes HFI < target_hfi
    # exit condition 2: FFMC of 0 still causes HFI > target_hfi
    # exit condition 3: relative error within 1%

    while abs(error_hfi) > 0.01:
        if experimental_ffmc >= 100.9 and experimental_hfi < target_hfi:
            break
        if experimental_ffmc <= 0.1:
            break
        if (
            error_hfi > 0
        ):  # if the error value is a positive number, make experimental FFMC value bigger
            experimental_ffmc = min(101, experimental_ffmc + ((101 - experimental_ffmc) / 2))
        else:  # if the error value is a negative number, need to make experimental FFMC value smaller
            experimental_ffmc = max(0, experimental_ffmc - ((101 - experimental_ffmc) / 2))
        experimental_isi = initial_spread_index(experimental_ffmc, wind_speed)
        experimental_sfc = surface_fuel_consumption(
            fuel_type, bui, experimental_ffmc, percentage_conifer
        )
        experimental_ros = rate_of_spread(
            fuel_type,
            experimental_isi,
            bui,
            fmc,
            experimental_sfc,
            percentage_conifer,
            grass_cure,
            percentage_dead_balsam_fir,
            crown_base_height,
        )
        experimental_hfi = head_fire_intensity(
            fuel_type,
            percentage_conifer,
            percentage_dead_balsam_fir,
            experimental_ros,
            cfb,
            cfl,
            experimental_sfc,
        )
        error_hfi = (target_hfi - experimental_hfi) / target_hfi

    return (experimental_ffmc, experimental_hfi)
