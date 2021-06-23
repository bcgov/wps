""" Unit testing for CFFDRS functions """
from app.utils import cffdrs


def test_ros():
    """ ROS runs """
    assert cffdrs.rate_of_spread("C7", 1, 1) == 1.2966988409822604e-05
