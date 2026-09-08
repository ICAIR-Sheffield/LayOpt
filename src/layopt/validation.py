"""Validation of configuration."""

import os
from pathlib import Path
from typing import Any

import cvxpy as cvx
import numpy as np
from loguru import logger
from schema import And, Or, Schema, SchemaError, SchemaWrongKeyError, Use


# pylint: disable=line-too-long
# pylint: disable=too-many-lines
def validate_config(config: dict[str, Any], schema: Schema, config_type: str) -> None:
    """
    Validate configuration.

    NB - This will fail on raw YAML files, the configuration should be passed through ``clean_config()`` first to
    convert configuration values to their expected types.

    Parameters
    ----------
    config : dict
        Config dictionary imported by ``read_yaml()`` and parsed through ``clean_config()``.
    schema : Schema
        A schema against which the configuration is to be compared.
    config_type : str
        Description of of configuration being validated.
    """
    try:
        schema.validate(config)
        logger.info(f"The {config_type} is valid.")
    except SchemaWrongKeyError:
        raise
    except SchemaError as schema_error:
        msg = (
            f"There is an error in your {config_type} configuration. "
            "Please refer to the first error message above for details"
        )
        raise SchemaError(msg) from schema_error


LAYOPT_CONFIG_SCHEMA = Schema(
    {
        "base_dir": Use(
            Path,
            error="Invalid value in config for 'base_dir', value should be type 'Path'.",
        ),
        "output_dir": Use(
            Path,
            error="Invalid value in config for 'output_dir', value should be type 'Path'.",
        ),
        "log_level": Or(
            "debug",
            "info",
            "warning",
            "error",
            error="Invalid value in config for 'log_level', valid values are 'info' (default), 'debug', 'error' or 'warning",
        ),
        "cores": lambda n: 1 <= n <= os.cpu_count(),
        "width": And(
            int,
            lambda n: n >= 1,
            error="Invalid value in config for 'width', valid values are int >= 1.",
        ),
        "height": And(
            int,
            lambda n: n >= 1,
            error="Invalid value in config for 'height', valid values are int >= 1.",
        ),
        "steps": Or(
            And(int, lambda n: n >= 1),
            And(float, lambda n: n > 0.0),
            error="Invalid value in config for 'steps', valid values are > 0.0.",
        ),
        "stress_tensile": Or(
            And(int, lambda n: n >= 0),
            And(float, lambda n: n >= 0.0),
            error="Invalid value in config for 'stress_tensile', valid values are >= 0.0.",
        ),
        "stress_compressive": Or(
            And(int, lambda n: n >= 0),
            And(float, lambda n: n >= 0.0),
            error="Invalid value in config for 'stress_compressive', valid values are >= 0.0.",
        ),
        "joint_cost": Or(
            And(int, lambda n: n >= 0),
            And(float, lambda n: n >= 0.0),
            error="Invalid value in config for 'joint_cost', valid values are >= 0.0",
        ),
        "youngs_modulus": Or(
            And(int, lambda n: n >= 0),
            And(float, lambda n: n >= 0.0),
            error="Invalid value in config for 'youngs_modulus', valid values are > 0.0",
        ),
        "avg_deflection_limit": Or(
            int,
            float,
            error="Invalid value in config for 'avg_deflection_limit', value should be type 'int' or 'float' (use a negative value to indicate plastic design).",
        ),
        "loaded_points": And(
            np.ndarray,
            lambda n: len(n.shape) == 2,
            error="Invalid value in config for 'loaded_points', should be a 2-dimensional array.",
        ),
        "load_direction": And(
            Or(list, tuple),
            lambda n: len(n) == 2,
            error="Invalid value in config for 'load_direction', should be a list|tuple of length 2.",
        ),
        "load_large": Or(
            And(int, lambda n: n >= 0),
            And(float, lambda n: n >= 0.0),
            error="Invalid value in config for 'load_large', valid values are >= 0.0.",
        ),
        "load_small": Or(
            And(int, lambda n: n >= 0),
            And(float, lambda n: n >= 0.0),
            error="Invalid value in config for 'load_small', valid values are >= 0.0.",
        ),
        "max_length": Or(
            And(int, lambda n: n >= 0),
            And(float, lambda n: n >= 0.0),
            error="Invalid value in config for 'max_length', valid values are >= 0.0.",
        ),
        "max_length_initial_ground_structure": And(
            float,
            lambda n: n > 0,
            error="Invalid value in config for 'max_length_initial_ground_structure', this should be a float > 0.",
        ),
        "support_points": And(
            np.ndarray,
            lambda n: n.size == 0 or (n.ndim == 2 and n.shape[1] == 4),
            lambda n: (
                n.size == 0
                or n.shape[1] != 4
                or set(np.unique(n[:, 2:4])).issubset({0.0, 1.0})
            ),
            error="Invalid value in config for 'support_points', this should be a list with each item in form '[x, y, restrain_x, restrain_y]' with 'restrain_x', 'restrain_y' being bool-like.",
        ),
        "member_area_filtering": Or(
            And(int, lambda n: 1 >= n >= 0),
            And(float, lambda n: 1.0 >= n >= 0.0),
            error="Invalid value in config for 'member_area_filtering', valid values are >= 0.0 and <= 1.0.",
        ),
        "cvxpy": {
            "solver": And(
                Use(lambda s: str(s).upper()),
                lambda s: s in cvx.installed_solvers(),
                error=f"Invalid value for 'solver', it should be one of your currently installed solvers: {cvx.installed_solvers()}.",
            ),
        },
        "filter_levels": And(
            np.ndarray,
            error="Invalid value for 'filter_levels', this should be an array of floats.",
        ),
        "primal_method": Or(
            And(
                str,
                Or(
                    "residual",
                    "load_factor",
                ),
            ),
            None,
            error="Invalid value in config for 'primal_methods', this should be 'residual', 'load_factor' or missing.",
        ),
        "problem_name": Use(
            str, error="Invalid value for 'problem_name', should be a string."
        ),
        "csv_filename": Use(
            str, error="Invalid value for 'csv_filename', should be a string."
        ),
        "notes": Use(str, error="Invalid value for 'notes', should be a string."),
        "plotting": {
            "run": And(
                bool,
                Or(True, False),
                error="Invalid value for 'plotting.run', should be a bool (True or False).",
            ),
            "bar_thickness": And(
                float,
                lambda n: n > 0.0,
                error="Invalid value for 'plotting.bar_thickness', should be a float > 0.0.",
            ),
            "dpi": And(
                int,
                lambda n: n >= 100,
                error="Invalid value for 'plotting.dpi', should be an int >= 100.",
            ),
        },
    }
)
