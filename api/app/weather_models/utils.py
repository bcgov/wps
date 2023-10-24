def construct_dictionary_from_list_by_property(source: list[any], property: any):
    """ Create a dictionary from a list where the dictionary keys are defined by the list item values of the provided
     property.
     :param source: The source list.
     :param property: A property name of the objects in the list.
    """
    result = {}
    for item in source:
        key = getattr(item, property)
        if key is None:
            continue
        if key not in result:
            result[key] = []
        result[key].append(item)
    return result
