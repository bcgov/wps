from app.utils.sfms import is_hfi_file, is_ffmc_file


def test_is_hfi_file():
    assert is_hfi_file('hfi20220824.tiff') is True


def test_is_not_hfi_file():
    assert is_hfi_file('at20220824.tiff') is False


def test_is_ffmc_file():
    assert is_ffmc_file('fine_fuel_moisture_code20220824.tiff') is True


def test_is_not_ffmc_file():
    assert is_ffmc_file('hfi20220824.tiff') is False