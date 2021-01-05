""" Util & common files for tests
"""
from typing import IO, Any, Callable
import os
import datetime
import json
import importlib
from app.db.models.common import TZTimeStamp


def _load_json_file(module_path: str, filename: str) -> dict:
    """ Load json file given a module path and a filename """
    dirname = os.path.dirname(os.path.realpath(module_path))
    with open(os.path.join(dirname, filename)) as file_pointer:
        return json.load(file_pointer)


def load_json_file_curried(module_path: str) -> Callable[[str], dict]:
    """ Return a function that can load json from a filename """
    def _json_loader(filename: str):
        return _load_json_file(module_path, filename)
    return _json_loader


def json_converter(item: object):
    """ Add datetime serialization """
    if isinstance(item, datetime.datetime):
        return item.isoformat()
    return None


def dump_sqlalchemy_response_to_json(response, target: IO[Any]):
    """ Useful for dumping sqlalchemy responses to json in for unit tests.

    e.g. if we want to store the response for GDPS predictions for two stations, we could write the
    following code:
    ```python
    query = get_station_model_predictions_order_by_prediction_timestamp(
        session, [322, 838], ModelEnum.GDPS, back_5_days, now)
    with open('tmp.json', 'w') as tmp:
        dump_sqlalchemy_response_to_json(query, tmp)
    ```
    """
    result = []
    for rows in response:
        result_row = []
        for record in rows:
            # Copy the dict so we can safely change it.
            data = dict(record.__dict__)
            # Pop internal value
            data.pop('_sa_instance_state')
            result_row.append(
                {
                    'module': type(record).__module__,
                    'class': type(record).__name__,
                    'data': data
                }
            )
        result.append(result_row)
    json.dump(result, fp=target, default=json_converter, indent=3)


def load_sqlalchemy_response_from_json(filename):
    """ Load a sqlalchemy response from a json file """
    with open(filename, 'r') as tmp:
        data = json.load(tmp)
    return load_sqlalchemy_response_from_object(data)


def de_serialize_record(record):
    """ De-serailize a single sqlalchemy record """
    module = importlib.import_module(record['module'])
    class_ = getattr(module, record['class'])
    record_data = {}
    for key, value in record['data'].items():
        # Handle the special case, where the type is timestamp, converting the string to the
        # correct data type.
        if isinstance(getattr(class_, key).type, TZTimeStamp):
            record_data[key] = datetime.datetime.fromisoformat(value)
        else:
            record_data[key] = value
    return class_(**record_data)


def load_sqlalchemy_response_from_object(data: object):
    """ Load a sqlalchemy response from an object """
    # Usualy the data is a list of objects - or a list of list of objects.
    # e.g.: [ { record }]
    # e.g.: or [ [{record}, {record}]]
    if isinstance(data, list):
        result = []
        for row in data:
            result_row = []
            for record in row:
                object_ = de_serialize_record(record)
                result_row.append(object_)
            result.append(result_row)
        return result
    # Sometimes though, we're only expecting a single record, not a list.
    return de_serialize_record(data)
