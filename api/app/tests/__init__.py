""" Util & common files
"""
from typing import IO, Any
import datetime
import json
import importlib
from app.db.models.common import TZTimeStamp


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


def load_sqlalchemy_response_from_object(data):
    """ Load a sqlalchemy response from an object """
    if isinstance(data, list):
        result = []
        for row in data:
            result_row = []
            for record in row:
                object_ = de_serialize_record(record)
                result_row.append(object_)
            result.append(result_row)
        return result
    return de_serialize_record(data)
