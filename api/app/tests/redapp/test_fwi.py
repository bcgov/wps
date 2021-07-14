import unittest
from app.utils.redapp import FWICalculateDailyStatisticsCOM
from app.utils.time import get_utc_now


class BasicFWITestCase(unittest.TestCase):
    """ Very dumb, very basic unit test that should really get replaced. """

    def test_fwi(self):
        """ veyr basic test """
        result = FWICalculateDailyStatisticsCOM(
            latitude=50.6733333,
            longitude=-120.4816667,
            yesterday_ffmc=50,
            yesterday_dmc=10,
            yesterday_dc=10,
            noon_temp=20,
            noon_rh=30,
            noon_precip=1,
            noon_wind_speed=20,
            calc_hourly=True,
            hourly_temp=20,
            hourly_rh=20,
            hourly_precip=1,
            hourly_wind_speed=10,
            previous_hourly_ffmc=50,
            use_van_wagner=False,
            use_lawson_previous_hour=True,
            time_of_interest=get_utc_now())
        self.assertIsNotNone(result)
