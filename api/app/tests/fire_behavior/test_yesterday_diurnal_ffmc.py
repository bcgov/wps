
from app.fire_behaviour.yesterday_diurnal_ffmc import YesterdayDiurnalFFMCLookupTable


def test_low_ffmc_below_55():
    result = YesterdayDiurnalFFMCLookupTable.instance().get(50, 6, 68)
    assert result == 47.6
