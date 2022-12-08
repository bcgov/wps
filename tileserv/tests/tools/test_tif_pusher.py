from unittest.mock import patch

from tileserv.tools.tif_pusher import get_filenames


@patch('os.listdir', return_value=["/path/HFI01012022.tiff", "/path/HFI02012022.tiff"])
def test_get_filenames_lowercase(_):
    assert get_filenames('tif_dir') == ["/path/hfi01012022.tiff", "/path/hfi02012022.tiff"]


@patch('os.listdir', return_value=["/path/bui01012022.tiff", "/path/hfi01012022.tiff"])
def test_get_filenames_only_hfi(_):
    assert get_filenames('tif_dir') == ["/path/hfi01012022.tiff"]


@patch('os.listdir', return_value=["/path/hfi01012022.tiff", "/path/hfi02012022.tiff"])
def test_get_filenames_all_hfi(_):
    assert get_filenames('tif_dir') == ["/path/hfi01012022.tiff", "/path/hfi02012022.tiff"]


@patch('os.listdir', return_value=["/path/hfi01012022.tif", "/path/hfi02012022.tiff"])
def test_get_filenames_tif_or_tiff(_):
    assert get_filenames('tif_dir') == ["/path/hfi01012022.tif", "/path/hfi02012022.tiff"]


@patch('os.listdir', return_value=["/path/hfi01012022.docx", "/path/hfi02012022.tiff"])
def test_get_filenames_ignore_non_tif(_):
    assert get_filenames('tif_dir') == ["/path/hfi02012022.tiff"]
