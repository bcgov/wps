"""Util & common files for tests"""

from typing import Callable, Optional
from dateutil import parser
import os
import json
import importlib
from wps_shared.db.models.common import TZTimeStamp


def get_complete_filename(module_path: str, filename: str):
    """Get the full path of a filename, given it's module path"""
    dirname = os.path.dirname(os.path.realpath(module_path))
    return os.path.join(dirname, filename)


def _load_json_file(module_path: str, filename: str) -> Optional[dict]:
    """Load json file given a module path and a filename"""
    if filename == "None":  # Not the best solution...
        return None
    if filename:
        with open(get_complete_filename(module_path, filename), encoding="utf-8") as file_pointer:
            return json.load(file_pointer)
    return None


def load_json_file(module_path: str) -> Callable[[str], dict]:
    """Return a function that can load json from a filename and return a dict"""

    def _json_loader(filename: str):
        return _load_json_file(module_path, filename)

    return _json_loader


def load_sqlalchemy_response_from_json(filename):
    """Load a sqlalchemy response from a json file"""
    with open(filename, "r", encoding="utf-8") as tmp:
        data = json.load(tmp)
    return load_sqlalchemy_response_from_object(data)


def de_serialize_record(record):
    """De-serailize a single sqlalchemy record"""
    module = importlib.import_module(record["module"])
    class_ = getattr(module, record["class"])
    record_data = {}
    for key, value in record["data"].items():
        # Handle the special case, where the type is timestamp, converting the string to the
        # correct data type.
        if isinstance(getattr(class_, key).type, TZTimeStamp):
            record_data[key] = parser.isoparse(value)
        else:
            record_data[key] = value
    return class_(**record_data)


def load_sqlalchemy_response_from_object(data: object):
    """Load a sqlalchemy response from an object"""
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
