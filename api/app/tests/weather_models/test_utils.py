from app.weather_models.utils import construct_dictionary_from_list_by_property


class TestObject:
    id: int
    name: str

    def __init__(self, id, name):
        self.id = id
        self.name = name


object_1 = TestObject(1, "foo")
object_2 = TestObject(2, "bar")
object_3 = TestObject(3, "foo")

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