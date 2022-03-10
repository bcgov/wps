from datetime import datetime
from pytest_bdd import scenario, given, when, then, parsers
from app.weather_models import interpolate_bearing


@scenario("test_interpolate_bearings.feature", "Interpolate bearings")
def test_direction_interpolation():
    """ BDD Scenario for directions """


@given(parsers.parse("{time_a}, {time_b}, {target_time}, {direction_a}, {direction_b}"),
       target_fixture='data',
       converters={
           'time_a': datetime.fromisoformat,
           'time_b': datetime.fromisoformat,
           'target_time': datetime.fromisoformat,
           'direction_a': float,
           'direction_b': float})
def given_data(
        time_a: datetime,
        time_b: datetime,
        target_time: datetime,
        direction_a: float,
        direction_b: float) -> dict:
    """ Collect data """
    return dict(
        time_a=time_a,
        time_b=time_b,
        target_time=target_time,
        direction_a=direction_a,
        direction_b=direction_b)


@when("You interpolate")
def when_interpolate(data: dict) -> float:
    """ Perform calculate """
    data['result'] = interpolate_bearing(**data)


@then(parsers.parse("You get {result}"), converters={'result': float})
def then_result(result: float, data: dict):
    """ Check results """
    assert result == data['result']
