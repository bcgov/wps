
import pytest
from app.fire_behaviour.yesterday_diurnal_ffmc import YesterdayDiurnalFFMCLookupTable


@pytest.mark.parametrize(
    "input_ffmc, hour, rh, expected_ffmc",
    [
        # early, 7am, lower rh
        (50, 7, 67, 53.5),
        (51, 7, 67, 53.5),
        (54, 7, 67, 53.5),
        (56, 7, 67, 56.9),

        # early, 7am, middle rh
        (50, 7, 68, 47.6),
        (51, 7, 68, 47.6),
        (54, 7, 68, 47.6),
        (56, 7, 68, 52.6),

        # early, 7am PDT, high rh
        (50, 7, 88, 42.9),
        (51, 7, 88, 42.9),
        (54, 7, 88, 42.9),
        (56, 7, 88, 48.5),

        # late, 1pm PDT, low rh
        (50, 13, 32, 82.4),
        (51, 13, 32, 82.4),
        (54, 13, 32, 82.4),
        (56, 13, 32, 83.2),

        # late, 1pm PDT, middle rh
        (50, 13, 33, 76.9),
        (51, 13, 33, 76.9),
        (54, 13, 33, 76.9),
        (56, 13, 33, 79.2),

        # late, 1pm PDT, high rh
        (50, 13, 53, 71.8),
        (51, 13, 53, 71.8),
        (54, 13, 53, 71.8),
        (56, 13, 53, 75.1),
    ],
)
def test_50_ffmc_range(input_ffmc, hour, rh, expected_ffmc):
    result = YesterdayDiurnalFFMCLookupTable.instance().get(input_ffmc, hour, rh)
    assert result == expected_ffmc


@pytest.mark.parametrize(
    "input_ffmc, hour, rh, expected_ffmc",
    [
        # early, 7am, lower rh
        (60, 7, 67, 56.9),
        (61, 7, 67, 56.9),
        (64, 7, 67, 56.9),
        (66, 7, 67, 61.7),

        # early, 7am, middle rh
        (60, 7, 68, 52.6),
        (61, 7, 68, 52.6),
        (64, 7, 68, 52.6),
        (66, 7, 68, 58.4),

        # early, 7am PDT, high rh
        (60, 7, 88, 48.5),
        (61, 7, 88, 48.5),
        (64, 7, 88, 48.5),
        (66, 7, 88, 55.1),

        # late, 1pm PDT, low rh
        (60, 13, 32, 83.2),
        (61, 13, 32, 83.2),
        (64, 13, 32, 83.2),
        (66, 13, 32, 85.2),

        # late, 1pm PDT, middle rh
        (60, 13, 33, 79.2),
        (61, 13, 33, 79.2),
        (64, 13, 33, 79.2),
        (66, 13, 33, 82.2),

        # late, 1pm PDT, high rh
        (60, 13, 53, 75.1),
        (61, 13, 53, 75.1),
        (64, 13, 53, 75.1),
        (66, 13, 53, 78.4),
    ],
)
def test_60_ffmc_range(input_ffmc, hour, rh, expected_ffmc):
    result = YesterdayDiurnalFFMCLookupTable.instance().get(input_ffmc, hour, rh)
    assert result == expected_ffmc


@pytest.mark.parametrize(
    "input_ffmc, hour, rh, expected_ffmc",
    [
        # early, 7am, lower rh
        (70, 7, 67, 61.7),
        (71, 7, 67, 61.7),
        (72, 7, 67, 62.9),

        # early, 7am, middle rh
        (70, 7, 68, 58.4),
        (71, 7, 68, 58.4),
        (72, 7, 68, 59.7),

        # early, 7am PDT, high rh
        (70, 7, 88, 55.1),
        (71, 7, 88, 55.1),
        (72, 7, 88, 56.5),

        # late, 1pm PDT, low rh
        (70, 13, 32, 83.2),
        (71, 13, 32, 83.2),
        (72, 13, 32, 85.2),

        # late, 1pm PDT, middle rh
        (70, 13, 33, 85.2),
        (71, 13, 33, 85.2),
        (72, 13, 33, 85.8),

        # late, 1pm PDT, high rh
        (70, 13, 53, 78.4),
        (71, 13, 53, 78.4),
        (72, 13, 53, 79.1),
    ],
)
def test_70_ffmc_range(input_ffmc, hour, rh, expected_ffmc):
    result = YesterdayDiurnalFFMCLookupTable.instance().get(input_ffmc, hour, rh)
    assert result == expected_ffmc


@pytest.mark.parametrize(
    "input_ffmc, hour, rh, expected_ffmc",
    [
        # early, 7am, lower rh
        (72, 7, 67, 62.9),
        (73, 7, 67, 64.1),
        (74, 7, 67, 64.1),

        # early, 7am, middle rh
        (72, 7, 68, 59.7),
        (73, 7, 68, 61.1),
        (74, 7, 68, 61.1),

        # early, 7am PDT, high rh
        (72, 7, 88, 56.5),
        (73, 7, 88, 58.0),
        (74, 7, 88, 58.0),

        # late, 1pm PDT, low rh
        (72, 13, 32, 85.8),
        (73, 13, 32, 86.5),
        (74, 13, 32, 86.5),

        # late, 1pm PDT, middle rh
        (72, 13, 33, 82.9),
        (73, 13, 33, 83.6),
        (74, 13, 33, 83.6),

        # late, 1pm PDT, high rh
        (72, 13, 53, 79.1),
        (73, 13, 53, 79.8),
        (74, 13, 53, 79.8),
    ],
)
def test_72_ffmc_range(input_ffmc, hour, rh, expected_ffmc):
    result = YesterdayDiurnalFFMCLookupTable.instance().get(input_ffmc, hour, rh)
    assert result == expected_ffmc


@pytest.mark.parametrize(
    "input_ffmc, hour, rh, expected_ffmc",
    [
        # early, 7am, lower rh
        (74, 7, 67, 64.1),
        (74.1, 7, 67, 64.8),

        # early, 7am, middle rh
        (74, 7, 68, 61.1),
        (74.1, 7, 68, 61.8),

        # early, 7am PDT, high rh
        (74, 7, 88, 58.0),
        (74.1, 7, 88, 58.8),

        # late, 1pm PDT, low rh
        (74, 13, 32, 86.5),
        (74.1, 13, 32, 86.8),

        # late, 1pm PDT, middle rh
        (74, 13, 33, 83.6),
        (74.1, 13, 33, 84.0),

        # late, 1pm PDT, high rh
        (74, 13, 53, 79.8),
        (74.1, 13, 53, 80.2),
    ],
)
def test_74_ffmc_range(input_ffmc, hour, rh, expected_ffmc):
    result = YesterdayDiurnalFFMCLookupTable.instance().get(input_ffmc, hour, rh)
    assert result == expected_ffmc


@pytest.mark.parametrize(
    "input_ffmc, hour, rh, expected_ffmc",
    [
        # early, 7am, lower rh
        (75, 7, 67, 64.8),
        (75.1, 7, 67, 65.5),

        # early, 7am, middle rh
        (75, 7, 68, 61.8),
        (75.1, 7, 68, 62.5),

        # early, 7am PDT, high rh
        (75, 7, 88, 58.8),
        (75.1, 7, 88, 59.5),

        # late, 1pm PDT, low rh
        (75, 13, 32, 86.8),
        (75.1, 13, 32, 87.2),

        # late, 1pm PDT, middle rh
        (75, 13, 33, 84.0),
        (75.1, 13, 33, 84.4),

        # late, 1pm PDT, high rh
        (75, 13, 53, 80.2),
        (75.1, 13, 53, 80.5),
    ],
)
def test_75_ffmc_range(input_ffmc, hour, rh, expected_ffmc):
    result = YesterdayDiurnalFFMCLookupTable.instance().get(input_ffmc, hour, rh)
    assert result == expected_ffmc


@pytest.mark.parametrize(
    "input_ffmc, hour, rh, expected_ffmc",
    [
        # early, 7am, lower rh
        (99, 7, 67, 91.9),
        (100, 7, 67, 93.2),

        # early, 7am, middle rh
        (99, 7, 68, 86.5),
        (100, 7, 68, 88.0),

        # early, 7am PDT, high rh
        (99, 7, 88, 84.1),
        (100, 7, 88, 85.4),

        # late, 1pm PDT, low rh
        (99, 13, 32, 97.1),
        (100, 13, 32, 97.9),

        # late, 1pm PDT, middle rh
        (99, 13, 33, 95.5),
        (100, 13, 33, 96.7),

        # late, 1pm PDT, high rh
        (99, 13, 53, 90.5),
        (100, 13, 53, 91.8),
    ],
)
def test_99_100_ffmc_range(input_ffmc, hour, rh, expected_ffmc):
    result = YesterdayDiurnalFFMCLookupTable.instance().get(input_ffmc, hour, rh)
    assert result == expected_ffmc
