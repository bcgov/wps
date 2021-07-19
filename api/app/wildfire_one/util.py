""" Utility functions used in several places within the wildfire_one module"""


def is_station_valid(station) -> bool:
    """ Run through a set of conditions to check if the station is valid.

    The RSQL filter is unable to filter on station status.

    Returns True if station is good, False is station is bad.
    """
    # In conversation with Dana Hicks, on Apr 20, 2021 - Dana said to show active, test and project.
    if not station.get('stationStatus', {}).get('id') in ('ACTIVE', 'TEST', 'PROJECT'):
        return False
    if station['latitude'] is None or station['longitude'] is None:
        # We can't use a station if it doesn't have a latitude and longitude.
        # pylint: disable=fixme
        # TODO : Decide if a station is valid if we can't determine its ecodivision and/or core fire season
        return False
    return True
