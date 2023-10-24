from app.weather_models.utils import construct_dictionary_from_list_by_property


object_1 = {"id": 1, "name": "foo"}
object_2 = {"id": 2, "name": "bar"}
object_3 = {"id": 3, "name": "foo"}

object_list = [object_1, object_2, object_3]


def test_construct_dictionary_from_list_by_property():
    result = construct_dictionary_from_list_by_property(object_list, "name")
    assert result is not None
    assert len(result.keys()) == 2
    assert len(result["foo"]) == 2
    assert len(result["bar"]) == 1
    assert object_1 in result["foo"]
    assert object_2 in result["bar"]
    assert object_3 in result["foo"]
