from datetime import datetime
from pytest_bdd import scenario, given, when, then
from app.weather_models import interpolate_bearing


@scenario("test_interpolate_bearings.feature", "Interpolate bearings",
          example_converters=dict(time_a=datetime.fromisoformat,
                                  time_b=datetime.fromisoformat,
                                  target_time=datetime.fromisoformat,
                                  direction_a=float,
                                  direction_b=float,
                                  result=float))
def test_direction_interpolation():
    """ BDD Scenario for directions """


@given("<time_a>, <time_b>, <target_time>, <direction_a>, <direction_b>", target_fixture='data')
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


@then("You get <result>")
def then_result(result: float, data: dict):
    """ Check results """
    assert result == data['result']
