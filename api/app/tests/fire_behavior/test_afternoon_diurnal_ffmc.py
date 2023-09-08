
from app.fire_behaviour.afternoon_diurnal_ffmc import AfternoonDiurnalFFMCLookupTable


def test_low_ffmc_below_55():
    result = AfternoonDiurnalFFMCLookupTable.instance().get(51, 13)
    assert result == 40.9


def test_ffmc_above_55_early():
    result = AfternoonDiurnalFFMCLookupTable.instance().get(56, 13)
    assert result == 48.2


def test_ffmc_above_55_late():
    result = AfternoonDiurnalFFMCLookupTable.instance().get(56, 7)
    assert result == 48.6


def test_ffmc_above_65_early():
    result = AfternoonDiurnalFFMCLookupTable.instance().get(65, 13)
    assert result == 57.3


def test_ffmc_above_65_late():
    result = AfternoonDiurnalFFMCLookupTable.instance().get(65, 7)
    assert result == 55.1


def test_ffmc_above_70_early():
    result = AfternoonDiurnalFFMCLookupTable.instance().get(71, 13)
    assert result == 59.4


def test_ffmc_above_70_late():
    result = AfternoonDiurnalFFMCLookupTable.instance().get(71, 7)
    assert result == 56.5


def test_ffmc_above_73_early():
    result = AfternoonDiurnalFFMCLookupTable.instance().get(74, 13)
    assert result == 61.7


def test_ffmc_above_73_late():
    result = AfternoonDiurnalFFMCLookupTable.instance().get(74, 7)
    assert result == 58.0


def test_ffmc_below_50_early():
    result = AfternoonDiurnalFFMCLookupTable.instance().get(49, 13)
    assert result is None


def test_ffmc_below_50_late():
    result = AfternoonDiurnalFFMCLookupTable.instance().get(49, 7)
    assert result is None


def test_ffmc_above_100_early():
    result = AfternoonDiurnalFFMCLookupTable.instance().get(101, 13)
    assert result == 97.9  # clamped to 100


def test_ffmc_above_100_late():
    result = AfternoonDiurnalFFMCLookupTable.instance().get(101, 7)
    assert result == 85.4  # clamped to 100
