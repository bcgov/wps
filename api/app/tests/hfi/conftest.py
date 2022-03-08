import json
from pytest_bdd import then, parsers
from app.tests import load_json_file


@then(parsers.parse("the response is {response_json}"), converters={'response_json': load_json_file(__file__)})
def then_response(result, response_json: dict):
    """ Check entire response """
    if response_json is not None:
        print('actual:\n{}'.format(json.dumps(result['response'].json(), indent=4)))
        print('expected:\n{}'.format(json.dumps(response_json, indent=4)))
        assert result['response'].json() == response_json, result['filename']


@then(parsers.parse("the response status code is {status_code}"), converters={'status_code': int})
def then_status(result, status_code: int):
    """ Check response status code """
    assert result['response'].status_code == status_code, result['filename']
