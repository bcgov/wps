""" Unit testing for CFFDRS functions """
import pytest
from app.utils import cffdrs


def test_ros():
    """ ROS runs """
    assert cffdrs.rate_of_spread("C7", 1, 1, 1, 1, pc=100, pdf=None,
                                 cc=None, cbh=10) == 1.2966988409822604e-05


def test_ros_no_isi():
    """ ROS fails """
    with pytest.raises(cffdrs.CFFDRSException):
        cffdrs.rate_of_spread("C7", None, 1, 1, 1, pc=100, pdf=None,
                              cc=None, cbh=10)


def test_ros_no_bui():
    """ ROS fails """
    with pytest.raises(cffdrs.CFFDRSException):
        cffdrs.rate_of_spread("C7", 1, None, 1, 1, pc=100, pdf=None,
                              cc=None, cbh=10)


def test_ros_no_params():
    """ ROS fails """
    with pytest.raises(cffdrs.CFFDRSException):
        cffdrs.rate_of_spread("C7", None, None, None, None, pc=100, pdf=None,
                              cc=None, cbh=10)
