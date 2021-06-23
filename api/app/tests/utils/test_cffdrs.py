""" Unit testing for CFFDRS functions """
from app.utils import cffdrs


def test_ros():
    """ ROS runs """
    assert cffdrs.rate_of_spread("C7", 1, 1) == 1.2966988409822604e-05


def test_ros_no_isi():
    """ ROS runs """
    assert cffdrs.rate_of_spread("C7", None, 1) == None


def test_ros_no_bui():
    """ ROS runs """
    assert cffdrs.rate_of_spread("C7", 1, None) == None


def test_ros_no_params():
    """ ROS runs """
    assert cffdrs.rate_of_spread("C7", None, None) == None
