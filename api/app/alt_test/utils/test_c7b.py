from app.fire_behaviour import c7b


def test_ros():
    # Test a few different rate of spread scenarios. This is more to ensure that
    # no accidental changes are made to the source code than to validate the
    # actual results. There's no external source of data to compare calculations
    # against.
    assert c7b.rate_of_spread(ffmc=93.9, bui=50, wind_speed=10,
                              percentage_slope=0, cc=20) == 0.048269559218302574
    assert c7b.rate_of_spread(ffmc=93.9, bui=100, wind_speed=10,
                              percentage_slope=0, cc=40) == 0.2271515401916674
    assert c7b.rate_of_spread(ffmc=93.9, bui=150, wind_speed=10,
                              percentage_slope=0, cc=80) == 2.6272848155902238
    assert c7b.rate_of_spread(ffmc=93.9, bui=201, wind_speed=10,
                              percentage_slope=0, cc=100) == 4.572887218615345
    assert c7b.rate_of_spread(ffmc=93.9, bui=201, wind_speed=20,
                              percentage_slope=0, cc=100) == 9.995513131014448
    assert c7b.rate_of_spread(ffmc=93.9, bui=201, wind_speed=20,
                              percentage_slope=10, cc=100) == 11.940438063156016
    # spreadsheet example 2.66:
    assert c7b.rate_of_spread(ffmc=93.9, bui=201, wind_speed=10,
                              percentage_slope=0, cc=80) == 2.6636471840719254
