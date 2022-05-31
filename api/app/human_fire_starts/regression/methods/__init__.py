""" Module containing different regression methods
"""
from dataclasses import dataclass
from typing import Any


@dataclass()
class ModelResult:
    """ Regression model, components and metrics
    """
    score: float
    mse: float
    rmse: float
    model: Any
    X_train: Any
    X_test: Any
    y_train: Any
    y_test: Any
    y_pred: Any
