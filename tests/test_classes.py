"""Tests for dataclasses."""

from contextlib import nullcontext as does_not_raise
from typing import Any

import numpy as np
import pytest
from pydantic import ValidationError

from layopt import classes


@pytest.mark.parametrize(
    ("config"),
    [
        pytest.param(
            {
                "filter_level": 1.0,
                "width": 1,
                "height": 1,
                "stress_tensile": 1,
                "stress_compressive": 1,
                "joint_cost": 0,
                "loaded_points": np.asarray([[3, 3]]),
                "load_direction": (0, -1),
                "load_large": 50,
                "load_small": 5,
                "max_length": 18,
                "support_points": np.asarray([[]]),
                "member_area_filtering": 0.001,
                "primal_method": "load_factor",
                "problem_name": "short cantilever",
                "save_to_csv": True,
                "csv_filename": "short_cantilever.csv",
                "notes": "short cantliever test",
            },
            id="1x1",
        ),
        pytest.param(
            {
                "filter_level": 1.0,
                "width": 1,
                "height": 1,
                "stress_tensile": 1,
                "stress_compressive": 1,
                "joint_cost": 0,
                "loaded_points": np.asarray([[3, 3]]),
                "load_direction": (0, -1),
                "load_large": 50,
                "load_small": 5,
                "max_length": 18,
                "support_points": np.asarray([[]]),
                "member_area_filtering": 0.001,
                "primal_method": "load_factor",
                "problem_name": "short cantilever",
                "save_to_csv": True,
                "csv_filename": "short_cantilever.csv",
                "notes": "short cantliever test",
            },
            id="2x2",
        ),
        pytest.param(
            {
                "filter_level": 1.0,
                "width": 3,
                "height": 6,
                "stress_tensile": 1,
                "stress_compressive": 1,
                "joint_cost": 0,
                "loaded_points": np.asarray([[3, 3]]),
                "load_direction": (0, -1),
                "load_large": 50,
                "load_small": 5,
                "max_length": 18,
                "support_points": np.asarray([[]]),
                "primal_method": "load_factor",
                "problem_name": "short cantilever",
                "save_to_csv": True,
                "csv_filename": "short_cantilever.csv",
                "notes": "short cantliever test",
            },
            id="3x6 cantilever",
        ),
        pytest.param(
            {
                "filter_level": 1.0,
                "width": 8,
                "height": 8,
                "stress_tensile": 1,
                "stress_compressive": 1,
                "joint_cost": 0,
                "loaded_points": np.asarray([[8, 0], [8, 4]]),
                "load_direction": (0, -1),
                "load_large": 50,
                "load_small": 5,
                "max_length": 15,
                "support_points": np.asarray([[]]),
                "primal_method": "load_factor",
                "problem_name": "square cantilever",
                "save_to_csv": True,
                "csv_filename": "square_cantilever.csv",
                "notes": "square cantliever test",
            },
            id="8x8 square cantilever",
        ),
        pytest.param(
            {
                "filter_level": 1.0,
                "width": 3,
                "height": 1,
                "stress_tensile": 1,
                "stress_compressive": 1,
                "joint_cost": 0,
                "loaded_points": np.asarray([[3, 0], [3, 1]]),
                "load_direction": (0, -1),
                "load_large": 50,
                "load_small": 5,
                "max_length": 2.5,
                "support_points": np.asarray([[]]),
                "primal_method": "load_factor",
                "problem_name": "parallel forces",
                "save_to_csv": True,
                "csv_filename": "parallel_forces.csv",
                "notes": "parallel forces test",
            },
            id="3x1 parallel forces",
        ),
        pytest.param(
            {
                "filter_level": 1.0,
                "width": 18,
                "height": 4,
                "stress_tensile": 1,
                "stress_compressive": 1,
                "joint_cost": 0,
                "loaded_points": np.asarray(
                    [
                        [6.0, 4],
                        [8.0, 4],
                        [12.0, 4],
                    ]
                ),
                "load_direction": (0, -1),
                "load_large": 3.75,
                "load_small": 0.204,
                "max_length": 36,
                "support_points": np.asarray([[0, 0], [18, 0]]),
                "primal_method": "load_factor",
                "problem_name": "spanning example",
                "save_to_csv": True,
                "csv_filename": "spanning_example.csv",
                "notes": "spanning example test",
            },
            id="18x4 spanning",
        ),
    ],
)
def test_parameters(config: dict[str:Any]) -> None:
    """Test instantiation of ``Parameters`` data class with test configurations."""
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
