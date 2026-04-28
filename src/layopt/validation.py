"""Validation of configuration."""

import os
from pathlib import Path
from typing import Any

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
        logger.info(f"✅ The {config_type} is valid.")
    except SchemaWrongKeyError:
        raise
    except SchemaError as schema_error:
        msg = (
            f"❌ There is an error in your {config_type} configuration. "
            "Please refer to the first error message above for details"
        )
        raise SchemaError(msg) from schema_error


LAYOPT_CONFIG_SCHEMA = Schema(
    {
        "base_dir": Use(
            Path,
            error="❌ Invalid value in config for 'base_dir', value should be type 'Path'.",
        ),
        "output_dir": Use(
            Path,
            error="❌ Invalid value in config for 'output_dir', value should be type 'Path'.",
        ),
        "log_level": Or(
            "debug",
            "info",
            "warning",
            "error",
            error="❌ Invalid value in config for 'log_level', valid values are 'info' (default), 'debug', 'error' or 'warning",
        ),
        "cores": lambda n: 1 <= n <= os.cpu_count(),
        "width": lambda n: n >= 1,
        "height": lambda n: n >= 1,
        "stress_tensile": Or(
            And(int, lambda n: n >= 0),
            And(float, lambda n: n >= 0.0),
            error="❌ Invalid value in config for 'stress_tensile', valid values are >= 0.0.",
        ),
        "stress_compressive": Or(
            And(int, lambda n: n >= 0),
            And(float, lambda n: n >= 0.0),
            error="❌ Invalid value in config for 'stress_compressive', valid values are >= 0.0.",
        ),
        "joint_cost": Or(
            And(int, lambda n: n >= 0),
            And(float, lambda n: n >= 0.0),
            error="❌ Invalid value in config for 'joint_cost', valid values are >= 0.0",
        ),
        "loaded_points": And(
            np.ndarray,
            lambda n: len(n.shape) == 2,
            error="❌ Invalid value in config for 'loaded_points', should be a 2-dimensional array.",
        ),
        "load_direction": And(
            tuple,
            lambda n: len(n) == 2,
            error="❌ Invalid value in config for 'load_direction', should be a tuple of length 2.",
        ),
        "load_large": Or(
            And(int, lambda n: n >= 0),
            And(float, lambda n: n >= 0.0),
            error="❌ Invalid value in config for 'load_large', valid values are >= 0.0.",
        ),
        "load_small": Or(
            And(int, lambda n: n >= 0),
            And(float, lambda n: n >= 0.0),
            error="❌ Invalid value in config for 'load_small', valid values are >= 0.0.",
        ),
        "max_length": Or(
            And(int, lambda n: n >= 0),
            And(float, lambda n: n >= 0.0),
            error="❌ Invalid value in config for 'max_length', valid values are >= 0.0.",
        ),
        "support_points": And(
            np.ndarray,
            lambda n: len(n.shape) == 2,
            error="❌ Invalid value in config for 'support_points', this should be a list of coordinates.",
        ),
        "filter_levels": And(
            np.ndarray,
            error="❌ Invalid value for 'filter_levels', this should be an array of floats.",
        ),
        "primal_method": And(
            str,
            Or(
                "residual",
                "load_factor",
                None,
            ),
            error="❌ Invalid value in config for 'primal_methods', this should be a list of coordinates.",
        ),
        "problem_name": Use(
            str, error="❌ Invalid value for 'problem_name', should be a string."
        ),
        "csv_filename": Use(
            str, error="❌ Invalid value for 'csv_filename', should be a string."
        ),
        "notes": Use(str, error="❌ Invalid value for 'notes', should be a string."),
        "plotting": {
            "run": And(
                bool,
                Or(True, False),
                error="❌ Invalid value for 'plotting.run', should be a bool (True or False).",
            ),
            "bar_thickness": And(
                float,
                lambda n: n > 0.0,
                error="❌ Invalid value for 'plotting.bar_thickness', should be a float > 0.0.",
            ),
            "dpi": And(
                int,
                lambda n: n >= 100,
                error="❌ Invalid value for 'plotting.dpi', should be an int >= 100.",
            ),
        },
    }
)
