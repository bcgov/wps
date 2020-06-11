""" Mocking calls to database for functional testing """
from pytest_bdd import scenario, given, then
from sqlalchemy import DateTime, cast
# TODO: Is this even a good one to use?
from alchemy_mock.mocking import UnifiedAlchemyMagicMock
from db import crud, models
import schemas


@scenario('test_crud.feature', 'Create a single forecast',
          example_converters=dict(
              issue_date=str,
              date_time=str,
              temperature=float,
              rh=float,
              wind_speed=float,
              total_precip=float,
              station_code=int
          ))
def test_create_single_forecast():
    # NOTE: Once we do CRUD through the API, relook this test.
    """ BDD Scenario. """

@given("I am a session creating a forecast with <date_time>, <temperature>, <rh>, <wind_speed>, <total_precip> at time <issue_date> for station <station_code>")
def create_single_forecast(date_time: str, temperature: float, rh: float, wind_speed: float,
                           total_precip: float, issue_date: str, station_code: int):
    """ Create a single forecast & mock adding it to the DB """
    session = UnifiedAlchemyMagicMock()  # TODO: How far do we take this?
    forecast = schemas.WeatherForecastValues(
        datetime=date_time,
        temperature=temperature,
        relative_humidity=rh,
        wind_speed=wind_speed,
        total_precipitation=total_precip)
    crud.create_single_forecast(session, forecast, issue_date, station_code)
    return (session, issue_date, temperature, station_code)

@then("The forecast should be committed to the database")
def response(create_single_forecast):
    """ Assert that the single forecast has been added to the DB """
    session, issue_date, temperature, station_code = create_single_forecast
    issue_date_datetime = cast(issue_date, DateTime)
    forecasts = session.query(models.SingleForecast).filter(models.SingleForecast.weather_station == station_code).filter(models.SingleForecast.issue_date == issue_date_datetime).all()
    assert forecasts[0].temperature == temperature
