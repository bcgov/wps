"""
Computatations for C7b Based on:
Spreadsheet originally created by J. Beck, 2003,
Updated (formatting, layout) by D. Perrakis, 2014

The spreadsheet can be found in the Predictive Services Unit Sharepoint site,
search for "NewC7b - C7 with curing3.xls"
"""
import math


def rate_of_spread(ffmc: float,  # excel column: C29
                   bui: float,  # excel column: C30
                   wind_speed: float,  # excel column: C37
                   percentage_slope: float,  # excel column: C38
                   cc: float,  # excel column: C17 (% curing) # pylint: disable=invalid-name
                   ):
    ''' Compute the rate of spread for the C7b fuel type
    Based on:
    Spreadsheet originally created by J. Beck, 2003,
    Updated (formatting, layout) by D. Perrakis, 2014

    TODO: This function can be further simplified by using only the caclulations that differ
    from the standard cffdrs R calculations.
    '''
    # we're using weird variable names to make debugging against excel spreadsheet easier:
    # pylint: disable=invalid-name

    # Calculated Curing Factor
    # C25: =1.25924/(1+EXP(-0.075*(C17-82)))
    calculated_curing_factor = 1.25924 / (1 + math.exp(-0.075 * (cc - 82)))

    # SF
    # C39: =EXP(3.533*(C38/100)^1.2)
    SF = math.exp(3.533 * math.pow((percentage_slope / 100), 1.2))

    # No Wind ISI
    # C42: =0.208*(91.9*EXP(-0.1386*(147.2*(101-C29)/(59.5+C29)))*(1+
    # (147.2*(101-C29)/(59.5+C29))^5.31/(4.93*10^7)))*EXP(0.05038*0)
    no_wind_isi = 0.208 * (91.9 * math.exp(-0.1386 * (147.2 * (101 - ffmc) / (59.5 + ffmc))) * (1 +
                           math.pow((147.2 * (101 - ffmc) / (59.5 + ffmc)), 5.31) / (4.93 * math.pow(10, 7)))
                           ) * math.exp(0.05038 * 0)

    # RSF with CF applied
    # C40: (45*(1-EXP(-0.0305*C42))^2)*C25*C39
    rsf_with_cf_applied = (45 * math.pow((1 - math.exp(-0.0305 * no_wind_isi)), 2)) * \
        calculated_curing_factor * SF

    # Calculated ISF with CF
    # C45: =LN(1-(C40/(C25*45))^(1/2))/-0.0305
    calculated_isf_with_cf = math.log(
        1 - math.pow((rsf_with_cf_applied / (calculated_curing_factor * 45)), (1 / 2))) / -0.0305

    # Calculated m
    # C46: =147.2*(101-C29)/(59.5+C29)
    calculated_m = 147.2 * (101 - ffmc) / (59.5 + ffmc)

    # Calculated f(F)
    # C47: =91.9*EXP(-0.1386*C46)*(1+(C46^5.31)/(4.93*10^7))
    calculated_f_f = 91.9 * math.exp(-0.1386 * calculated_m) * \
        (1 + (math.pow(calculated_m, 5.31)) / (4.93 * math.pow(10, 7)))

    # Calculated WSE with CF
    # C49: =LN(C45/(0.208*C47))/0.05039
    calculated_wse_with_cf = math.log(calculated_isf_with_cf / (0.208 * calculated_f_f)) / 0.05039

    # Net Effective Wind Speed
    # C50: =C49+C37
    net_effective_wind_speed = calculated_wse_with_cf + wind_speed

    # ISI adjusted for Slope and Wind
    # C51: =0.208*(91.9*EXP(-0.1386*(147.2*(101-C29)/(59.5+C29)))*(1+(147.2*(101-C29)/(59.5+C29))
    # ^5.31/(4.93*10^7)))*EXP(0.05038*C50)
    isi_adjusted_for_slope_and_wind = 0.208 * (91.9 * math.exp(
        -0.1386 * (147.2 * (101 - ffmc) / (59.5 + ffmc))) * (1 + math.pow(
            (147.2 * (101 - ffmc) / (59.5 + ffmc)), 5.31) / (4.93 * math.pow(10, 7)))) * math.exp(
                0.05038 * net_effective_wind_speed)

    # Slope and Wind adjusted RSI
    # C52: =(45*(1-EXP(-0.0305*C51))^2)*C25
    slope_and_wind_adjusted_rsi = (
        45 * math.pow((1 - math.exp(
            -0.0305 * isi_adjusted_for_slope_and_wind)), 2)) * calculated_curing_factor

    # BE
    # C53: BE=EXP(50*LN(0.85)*(1/C30-1/106))
    BE = math.exp(50 * math.log(0.85) * (1 / bui - 1 / 106))

    # C54: =C52*C53
    return slope_and_wind_adjusted_rsi * BE
