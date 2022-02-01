"""
Computatations for C7b Based on:
Spreadsheet originally created by J. Beck, 2003,
Updated (formatting, layout) by D. Perrakis, 2014
"""
from math import exp, log, pow


def rate_of_spread(ffmc: float,  # excel column: C29
                   bui: float,  # excel column: C30
                   wind_speed: float,  # excel column: C37
                   percentage_slope: float,  # excel column: C38
                   cc: float,  # excel column: C17 (% curing)
                   ):
    ''' Compute the rate of spread for the C7b fuel type 
    Based on:
    Spreadsheet originally created by J. Beck, 2003,
    Updated (formatting, layout) by D. Perrakis, 2014
    '''

    # Calculated Curing Factor
    # C25: =1.25924/(1+EXP(-0.075*(C17-82)))
    calculated_curing_factor = 1.25924 / (1 + exp(-0.075 * (cc - 82)))

    # SF
    # C39: =EXP(3.533*(C38/100)^1.2)
    SF = exp(3.533 * pow((percentage_slope / 100), 1.2))

    # No Wind ISI
    # C42: =0.208*(91.9*EXP(-0.1386*(147.2*(101-C29)/(59.5+C29)))*(1+(147.2*(101-C29)/(59.5+C29))^5.31/(4.93*10^7)))*EXP(0.05038*0)
    no_wind_ISI = 0.208 * (91.9 * exp(-0.1386 * (147.2 * (101 - ffmc) / (59.5 + ffmc))) * (1 +
                           pow((147.2 * (101 - ffmc) / (59.5 + ffmc)), 5.31) / (4.93 * pow(10, 7)))) * exp(0.05038 * 0)

    # RSF with CF applied
    # C40: (45*(1-EXP(-0.0305*C42))^2)*C25*C39
    RSF_with_CF_applied = (45 * pow((1 - exp(-0.0305 * no_wind_ISI)), 2)) * calculated_curing_factor * SF

    # Calculated ISF with CF
    # C45: =LN(1-(C40/(C25*45))^(1/2))/-0.0305
    calculated_ISF_with_CF = log(
        1 - pow((RSF_with_CF_applied / (calculated_curing_factor * 45)), (1 / 2))) / -0.0305

    # Calculated m
    # C46: =147.2*(101-C29)/(59.5+C29)
    calculated_m = 147.2 * (101 - ffmc) / (59.5 + ffmc)

    # Calculated f(F)
    # C47: =91.9*EXP(-0.1386*C46)*(1+(C46^5.31)/(4.93*10^7))
    calculated_f_F = 91.9 * exp(-0.1386 * calculated_m) * \
        (1 + (pow(calculated_m, 5.31)) / (4.93 * pow(10, 7)))

    # Calculated WSE with CF
    # C49: =LN(C45/(0.208*C47))/0.05039
    calculated_WSE_with_CF = log(calculated_ISF_with_CF / (0.208 * calculated_f_F)) / 0.05039

    # Net Effective Wind Speed
    # C50: =C49+C37
    net_effective_wind_speed = calculated_WSE_with_CF + wind_speed

    # ISI adjusted for Slope and Wind
    # C51: =0.208*(91.9*EXP(-0.1386*(147.2*(101-C29)/(59.5+C29)))*(1+(147.2*(101-C29)/(59.5+C29))^5.31/(4.93*10^7)))*EXP(0.05038*C50)
    isi_adjusted_for_slope_and_wind = 0.208 * (91.9 * exp(-0.1386 * (147.2 * (101 - ffmc) / (59.5 + ffmc))) * (1 + pow(
        (147.2 * (101 - ffmc) / (59.5 + ffmc)), 5.31) / (4.93 * pow(10, 7)))) * exp(0.05038 * net_effective_wind_speed)

    # Slope and Wind adjusted RSI
    # C52: =(45*(1-EXP(-0.0305*C51))^2)*C25
    slope_and_wind_adjusted_RSI = (
        45 * pow((1 - exp(-0.0305 * isi_adjusted_for_slope_and_wind)), 2)) * calculated_curing_factor

    # BE
    # C53: BE=EXP(50*LN(0.85)*(1/C30-1/106))
    BE = exp(50 * log(0.85) * (1 / bui - 1 / 106))

    # C54: =C52*C53
    return slope_and_wind_adjusted_RSI * BE


if __name__ == '__main__':
    # quick sanity check to see if getting the same values as spreadsheet.
    ros = rate_of_spread(0, 201, 0, 0, 0, 80, 0, 0)
    print(f'ros: {ros}')
