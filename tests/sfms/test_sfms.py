from auto_spatial_advisory.sfms import get_prefix, is_hfi_file


def test_is_hfi_file():
    assert is_hfi_file('hfi20220824.tiff') is True


def test_is_not_hfi_file():
    assert is_hfi_file('at20220824.tiff') is False
