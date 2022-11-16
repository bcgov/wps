""" Util & common files for tests
"""
from typing import IO, Any, Callable, Optional, Tuple
import os
import sys
import datetime
import json
import importlib
import jsonpickle
from db.models.common import TZTimeStamp


def get_complete_filename(module_path: str, filename: str):
    """ Get the full path of a filename, given it's module path """
    dirname = os.path.dirname(os.path.realpath(module_path))
    return os.path.join(dirname, filename)


def _load_json_file(module_path: str, filename: str) -> Optional[dict]:
    """ Load json file given a module path and a filename """
    if filename == 'None':  # Not the best solution...
        return None
    if filename:
        with open(get_complete_filename(module_path, filename), encoding="utf-8") as file_pointer:
            return json.load(file_pointer)
    return None


def _load_json_file_with_name(module_path: str, filename: str) -> Tuple[Optional[dict], str]:
    """ Load json file given a module path and a filename """
    if filename == 'None':  # Not the best solution...
        return None, filename
    if filename:
        with open(get_complete_filename(module_path, filename), encoding="utf-8") as file_pointer:
            return json.load(file_pointer), filename
    return None, filename


def load_json_file(module_path: str) -> Callable[[str], dict]:
    """ Return a function that can load json from a filename and return a dict """
    def _json_loader(filename: str):
        return _load_json_file(module_path, filename)
    return _json_loader


def load_json_file_with_name(module_path: str) -> Callable[[str], dict]:
    """ Return a function that can load a json from a filename and return a dict, but also the filename """
    def _json_loader(filename: str):
        return _load_json_file_with_name(module_path, filename)
    return _json_loader


def json_converter(item: object):
    """ Add datetime serialization """
    if isinstance(item, datetime.datetime):
        return item.isoformat()
    return None


def dump_sqlalchemy_row_data_to_json(response, target: IO[Any]):
    """ Useful for dumping sqlalchemy responses to json in for unit tests. """
    result = []
    for response_row in response:
        result.append(jsonpickle.encode(response_row))
    target.write(jsonpickle.encode(result))


def dump_sqlalchemy_mapped_object_response_to_json(response, target: IO[Any]):
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
    for row in response:
        result_row = []
        for record in row:
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
    with open(filename, 'r', encoding="utf-8") as tmp:
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


def apply_crud_mapping(monkeypatch, crud_mapping: dict, module_path: str):
    """ Mock the sql response
    The crud response was generated by temporarily introducing
    "dump_sqlalchemy_row_data_to_json" and "dump_sqlalchemy_mapped_object_response_to_json"
    in code - and saving the database responses.
    """

    if crud_mapping:
        for item in crud_mapping:
            if item['serializer'] == "jsonpickle":
                _jsonpickle_patch_function(monkeypatch,
                                           item['module'], item['function'], item['json'], module_path)
            else:
                _json_patch_function(monkeypatch,
                                     item['module'], item['function'], item['json'], module_path)

    return {}


def _jsonpickle_patch_function(
        monkeypatch,
        module_name: str,
        function_name: str,
        json_filename: str,
        module_path: str):
    """ Patch module_name.function_name to return de-serialized json_filename """
    def mock_get_data(*_):
        filename = get_complete_filename(module_path, json_filename)
        with open(filename, encoding="utf-8") as file_pointer:
            rows = jsonpickle.decode(file_pointer.read())
            for row in rows:
                # Workaround to remain compatible with old tests. Ideally we would just always pickle the row.
                if isinstance(row, str):
                    yield jsonpickle.decode(row)
                    continue
                yield row

    monkeypatch.setattr(importlib.import_module(module_name), function_name, mock_get_data)


def _json_patch_function(monkeypatch,
                         module_name: str,
                         function_name: str,
                         json_filename: str,
                         module_path: str):
    """ Patch module_name.function_name to return de-serialized json_filename """
    def mock_get_data(*_):
        filename = get_complete_filename(module_path, json_filename)
        with open(filename, encoding="utf-8") as file_pointer:
            return json.load(file_pointer)

    monkeypatch.setattr(importlib.import_module(module_name), function_name, mock_get_data)
