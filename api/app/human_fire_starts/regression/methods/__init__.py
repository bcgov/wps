""" Module containing different regression methods
"""
from dataclasses import dataclass
from enum import Enum
from typing import Any


class RegressionMethod(str, Enum):
    RANDOM_FOREST = 'Random Forest'
    GRADIENT_BOOST = 'Gradient Boost'
    EXTRA_TREES = 'Extra Trees'
    BAGGING = 'Bagging'
    ADA = 'Ada'
    HIST_GRADIENT_BOOST = 'Histogram Gradient Boost'
    LINEAR = "Linear"


@dataclass()
class ModelResult:
    """ Regression model, components and metrics
    """
    score: float
    mse: float
    rmse: float
    model: Any
    cv_results: Any
    X_train: Any
    X_test: Any
    y_train: Any
    y_test: Any
    y_pred: Any
