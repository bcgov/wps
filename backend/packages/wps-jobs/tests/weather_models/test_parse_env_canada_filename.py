"""Tests for Environment Canada filename parsing"""

import logging
import pytest
from weather_model_jobs.env_canada import parse_env_canada_filename

logger = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "filename,projection,variable_name",
    [
        ("CMC_glb_TMP_TGL_2_latlon.24x.24_2020070212_P240.grib2", "latlon.24x.24", "TMP_TGL_2"),
        (
            "CMC_glb_ABSV_ISBL_200_latlon.24x.24_2020070600_P000.grib2",
            "latlon.24x.24",
            "ABSV_ISBL_200",
        ),
        (
            "CMC_glb_ABSV_ISBL_200_latlon.15x.15_2020070600_P000.grib2",
            "latlon.15x.15",
            "ABSV_ISBL_200",
        ),
        ("CMC_glb_RH_TGL_2_latlon.15x.15_2020070712_P000.grib2", "latlon.15x.15", "RH_TGL_2"),
        (
            "/somewhere_on/the_drive/CMC_glb_RH_TGL_2_latlon.15x.15_2020070712_P000.grib2",
            "latlon.15x.15",
            "RH_TGL_2",
        ),
    ],
)
def test_parse_filename(filename, projection, variable_name):
    """
    _summary_

    :param filename: filename to parse
    :param projection: expected projection
    :param variable_name: expected weather variable
    """
    parsed_file = parse_env_canada_filename(filename)
    assert parsed_file.projection == projection
    assert parsed_file.variable_name == variable_name
