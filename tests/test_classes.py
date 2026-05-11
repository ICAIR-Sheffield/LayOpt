"""Tests for dataclasses."""

from contextlib import nullcontext as does_not_raise

import numpy as np
import pytest
from pydantic import ValidationError

from layopt import classes


@pytest.mark.parametrize(
    ("config_str"),
    [
        pytest.param("trussopt_param_one_by_one", id="1x1"),
        pytest.param("trussopt_param_two_by_two", id="2x2"),
        pytest.param(
            "trussopt_param_three_by_six_short_cantilever", id="3x6 cantilever"
        ),
        pytest.param(
            "trussopt_param_eight_by_eight_square_cantilever",
            id="8x8 square cantilever",
        ),
        pytest.param(
            "trussopt_param_three_by_one_parallel_forces", id="3x1 parallel forces"
        ),
        pytest.param("trussopt_param_eighteen_by_four_spanning", id="18x4 spanning"),
    ],
)
def test_parameters(config_str: str, request) -> None:
    """Test instantiation of ``Parameters`` data class with test configurations."""
    # Load config and tidy (normally done via config.reconcile_config_args() but want this test to remain independent
    config = request.getfixturevalue(config_str)
    for to_convert in ["loaded_points", "support_points", "load_direction"]:
        config[to_convert] = np.asarray(config[to_convert])
    with does_not_raise():
        classes.Parameters(**config)


@pytest.mark.parametrize(
    ("config"),
    [
        pytest.param({"width": "two"}, id="width as string"),
        pytest.param({"cores": 1.5}, id="cores as float"),
        pytest.param({"loaded_points": [[3, 3]]}, id="loaded_points as nested list"),
        pytest.param(
            {"joint_cost": 10},
            id="joint_cost as int",
            marks=pytest.mark.xfail(reason="Doesn't raise ValidationError"),
        ),
        pytest.param({"load_large": 1001.0}, id="load_large exceed upper limit"),
        pytest.param({"load_small": -1.0}, id="load_small negative"),
        pytest.param(
            {"loaded_points": np.asarray([[1.1, 3.14]], dtype=np.float64)},
            id="loaded_points as numpy array of floats",
            marks=pytest.mark.xfail(reason="Doesn't raise ValidationError"),
        ),
    ],
)
def test_parameters_exceptions(config: ValidationError) -> None:
    """Test exceptions are raised when invalid configurations are passed to ``Parameters`` class."""
    with pytest.raises(ValidationError):
        classes.Parameters(**config)
