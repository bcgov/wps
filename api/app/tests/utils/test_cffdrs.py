""" Unit testing for CFFDRS functions """
import pytest
from rpy2.rinterface import NULL
from app.schemas.fba_calc import FuelTypeEnum
from app.utils import cffdrs
import numpy as np


def test_foliar_moisture_content():
    """ FMC is calculated """
    expected = [85, 85]
    result = cffdrs.foliar_moisture_content(np.array([0, 1]), np.array(
        [0, 1]), np.array([0, 1]), np.array([0, 1]), np.array([0, 1]))
    assert len(result) == 2
    assert all([a == b for a, b in zip(result, expected)])


def test_surface_fuel_consumption_none_failures():
    """ SFC fails for required parameters """
    with pytest.raises(cffdrs.CFFDRSException):
        cffdrs.surface_fuel_consumption([None, FuelTypeEnum.C1], [0, 1], [0, 1], [0, 1])

    with pytest.raises(cffdrs.CFFDRSException):
        cffdrs.surface_fuel_consumption([FuelTypeEnum.C1, FuelTypeEnum.C1], [None, 1], [0, 1], [0, 1])

    with pytest.raises(cffdrs.CFFDRSException):
        cffdrs.surface_fuel_consumption([FuelTypeEnum.C1, FuelTypeEnum.C1], [0, 1], [None, 1], [0, 1])


def test_surface_fuel_consumption_list():
    """ SFC is calculated """
    expected = [1.525674475644223e-09, 1.9202138767937527e-09]
    result = cffdrs.surface_fuel_consumption([FuelTypeEnum.C1, FuelTypeEnum.C1], [0, 1], [0, 1], [0, 1])
    assert len(result) == 2
    assert all([a == b for a, b in zip(result, expected)])


def test_lb_ratio():
    """ LB ratio is calculated """
    expected = [1.0, 1.0044173043651534]
    result = cffdrs.length_to_breadth_ratio([FuelTypeEnum.C1, FuelTypeEnum.C1], [0, 1])
    assert len(result) == 2
    assert all([a == b for a, b in zip(result, expected)])


def test_lb_ratio_none_failures():
    """ LB ratio fails for required parameters """
    with pytest.raises(cffdrs.CFFDRSException):
        cffdrs.length_to_breadth_ratio([None, FuelTypeEnum.C1], [0, 1])

    with pytest.raises(cffdrs.CFFDRSException):
        cffdrs.length_to_breadth_ratio([FuelTypeEnum.C1, FuelTypeEnum.C1], np.array([None, 1]))


def test_rate_of_spread():
    """ ROS is calculated """
    expected = [1.e-06, 1.e-06]

    result = cffdrs.rate_of_spread([FuelTypeEnum.C1, FuelTypeEnum.C1], [0, 0], [0, 0], [
                                   0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0])
    assert len(result) == 2
    assert all([a == b for a, b in zip(result, expected)])


def test_rate_of_spread_failures():
    """ ROS fails for required parameters """
    with pytest.raises(cffdrs.CFFDRSException):
        cffdrs.rate_of_spread([None, FuelTypeEnum.C1],
                              [0, 1],
                              [0, 1],
                              [0, 1],
                              [0, 1],
                              [0, 1],
                              [0, 1],
                              [0, 1],
                              [0, 1])
    with pytest.raises(cffdrs.CFFDRSException):
        cffdrs.rate_of_spread([FuelTypeEnum.C1, FuelTypeEnum.C1],
                              [None, 1],
                              [0, 1],
                              [0, 1],
                              [0, 1],
                              [0, 1],
                              [0, 1],
                              [0, 1],
                              [0, 1])
    with pytest.raises(cffdrs.CFFDRSException):
        cffdrs.rate_of_spread([FuelTypeEnum.C1, FuelTypeEnum.C1],
                              [0, 1],
                              [None, 1],
                              [0, 1],
                              [0, 1],
                              [0, 1],
                              [0, 1],
                              [0, 1],
                              [0, 1])
    with pytest.raises(cffdrs.CFFDRSException):
        cffdrs.rate_of_spread([FuelTypeEnum.C1, FuelTypeEnum.C1],
                              [0, 1],
                              [0, 1],
                              [0, 1],
                              [None, 1],
                              [0, 1],
                              [0, 1],
                              [0, 1],
                              [0, 1])


@pytest.mark.skip(reason="Complains about scalar operator on vector")
def test_cfb():
    """ CFB is calculated TODO Fix"""
    result = cffdrs.crown_fraction_burned([FuelTypeEnum.D1, FuelTypeEnum.D1],
                                          [0, 1], [0, 1], [0, 1], [100, 100])
    assert len(result) == 2


def test_cfb_failures():
    with pytest.raises(cffdrs.CFFDRSException):
        cffdrs.crown_fraction_burned([FuelTypeEnum.C1, FuelTypeEnum.C1], [None, 1], [0, 1], [0, 1], [0, 1])

    with pytest.raises(cffdrs.CFFDRSException):
        cffdrs.crown_fraction_burned([FuelTypeEnum.C1, FuelTypeEnum.C1], [0, 1], [0, 1], [0, 1], [None, 1])


def test_rate_of_spread_t():
    """ ROS_t is calculated"""
    expected = [0.0, 0.9989922145709514]
    result = cffdrs.rate_of_spread_t([FuelTypeEnum.D1, FuelTypeEnum.D1], [0, 1], 60, [0, 1])
    assert len(result) == 2
    assert all([a == b for a, b in zip(result, expected)])


def test_total_fuel_consumption():
    """ TFC is calculated"""
    expected = [0, 2]
    result = cffdrs.total_fuel_consumption([FuelTypeEnum.C1, FuelTypeEnum.C1], [
                                           0, 1], [0, 1], [0, 1], [0, 1], [0, 1])
    assert len(result) == 2
    assert all([a == b for a, b in zip(result, expected)])


def test_total_fuel_consumption_failures():
    """ TFC fails for required parameters """
    with pytest.raises(cffdrs.CFFDRSException):
        cffdrs.total_fuel_consumption([FuelTypeEnum.C1, FuelTypeEnum.C1], [
                                      None, 1], [0, 1], [0, 1], [0, 1], [0, 1])

    with pytest.raises(cffdrs.CFFDRSException):
        cffdrs.total_fuel_consumption([FuelTypeEnum.C1, FuelTypeEnum.C1], [
                                      0, 1], [0, 1], [0, 1], [0, 1], [None, 1])


def test_hfi():
    """ HFI is calculated"""
    expected = [0, 600]
    result = cffdrs.head_fire_intensity([FuelTypeEnum.C1, FuelTypeEnum.C1], [0, 1], [
                                        0, 1], [0, 1], [0, 1], [0, 1], [0, 1])
    assert len(result) == 2
    assert all([a == b for a, b in zip(result, expected)])
