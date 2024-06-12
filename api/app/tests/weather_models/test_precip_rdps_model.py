import os
import numpy as np
import pytest
from datetime import datetime
from app.tests.utils.raster_reader import read_raster_array

from app.weather_models.precip_rdps_model import TemporalPrecip, compute_precip_difference

def test_difference_identity():
    """
    Verify difference of accumulated precip is zero when diffing the same raster
    """
    parent_dir = os.path.dirname(__file__)
    precip_raster = read_raster_array(os.path.join(parent_dir, "CMC_reg_APCP_SFC_0_ps10km_2024061218_P001.grib2"))
    later_precip = TemporalPrecip(datetime.fromisoformat("2024-06-10T18:42:49"), precip_raster)
    earlier_precip = TemporalPrecip(datetime.fromisoformat("2024-06-09T18:42:49"), precip_raster)

    res = compute_precip_difference(later_precip, earlier_precip)
    assert np.allclose(res, np.zeros(precip_raster.shape))

@pytest.mark.parametrize(
    'later_datetime,earlier_datetime',
    [
        (datetime.fromisoformat("2024-06-10T18:42:49"), datetime.fromisoformat("2024-06-10T18:42:49")), # same datetime
        (datetime.fromisoformat("2024-06-09T18:42:49"), datetime.fromisoformat("2024-06-10T18:42:49")) # later earlier than earlier
    ],
)
def test_temporal_assertion_failures(later_datetime, earlier_datetime):
    """
    Verify ValueError raised for wrong datetime arguments
    """
    parent_dir = os.path.dirname(__file__)
    precip_raster = read_raster_array(os.path.join(parent_dir, "CMC_reg_APCP_SFC_0_ps10km_2024061218_P001.grib2"))
    later_precip = TemporalPrecip(later_datetime, precip_raster)
    earlier_precip = TemporalPrecip(earlier_datetime, precip_raster)

    with pytest.raises(ValueError) as excinfo:
        compute_precip_difference(later_precip, earlier_precip)
    
    assert excinfo.value.args[0] == 'Later precip value must be after earlier precip value'
