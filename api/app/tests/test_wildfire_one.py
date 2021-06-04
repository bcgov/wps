""" Unit testing for WFWX API code """
from app.wildfire_one import BuildQueryAllHourliesByRange


def test_build_all_hourlies_query():
    """ Verifies the query builder returns the correct url and parameters """
    query_builder = BuildQueryAllHourliesByRange(0, 1)
    result = query_builder.query(0)
    assert result == ["https://wf1/wfwx/v1/hourlies/rsql",
                      {'size': '1000', 'page': 0, 'query': 'weatherTimestamp >=0;weatherTimestamp <1'}]
