from app.utils import c7b


def test_ros():
    assert c7b.rate_of_spread(ffmc=93.9, bui=50, wind_speed=10,
                              percentage_slope=0, cc=20) == 0.048269559218302574
    assert c7b.rate_of_spread(ffmc=93.9, bui=100, wind_speed=10,
                              percentage_slope=0, cc=40) == 0.2271515401916674
    assert c7b.rate_of_spread(ffmc=93.9, bui=150, wind_speed=10,
                              percentage_slope=0, cc=80) == 2.6272848155902238
    assert c7b.rate_of_spread(ffmc=93.9, bui=201, wind_speed=10,
                              percentage_slope=0, cc=100) == 4.572887218615345
