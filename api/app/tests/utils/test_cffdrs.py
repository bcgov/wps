""" Unit testing for CFFDRS functions """
import pytest
from app.utils import cffdrs


def test_ros(monkeypatch, mock_cffdrs):
    """ ROS runs """
    assert cffdrs.rate_of_spread("C7", 1, 1, 1, 1) == 1.2966988409822604e-05


def test_ros_no_isi(monkeypatch, mock_cffdrs):
    """ ROS fails """
    with pytest.raises(cffdrs.CFFDRSException):
        cffdrs.rate_of_spread("C7", None, 1, 1, 1)


def test_ros_no_bui(monkeypatch, mock_cffdrs):
    """ ROS fails """
    with pytest.raises(cffdrs.CFFDRSException):
        cffdrs.rate_of_spread("C7", 1, None, 1, 1)


def test_ros_no_params(monkeypatch, mock_cffdrs):
    """ ROS fails """
    with pytest.raises(cffdrs.CFFDRSException):
        cffdrs.rate_of_spread("C7", None, None, None, None)
