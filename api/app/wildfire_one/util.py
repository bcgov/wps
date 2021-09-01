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


def get_zone_code_prefix(fire_centre_id: int):
    """ Returns the single-letter code corresponding to fire centre.
    Used in constructing zone codes.
    Fire centre-to-letter mappings provided by Eric Kopetski.
    """
    fire_centre_to_zone_code_prefix = {
        25: 'K',            # Kamloops Fire Centre
        8: 'G',             # Prince George Fire Centre
        42: 'R',            # Northwest Fire Centre
        2: 'C',             # Cariboo Fire Centre
        34: 'N',            # Southeast Fire Centre
        50: 'V'             # Coastal Fire Centre
    }
    return fire_centre_to_zone_code_prefix.get(fire_centre_id, None)
