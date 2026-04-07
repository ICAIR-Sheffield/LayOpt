"""Test the config module functions."""

import argparse
import logging
from pathlib import Path
from pkgutil import get_data
from typing import Any

import numpy as np
import numpy.typing as npt
import pytest
import yaml
from schema import SchemaError

from layopt.config import (
    merge_mappings,
    reconcile_config_args,
)
from layopt.validation import LAYOPT_CONFIG_SCHEMA, validate_config

BASE_DIR = Path.cwd()
RESOURCES = BASE_DIR / "tests" / "resources"

# Load the 'default_config.yaml' to dictionary.
default_config = get_data(package="layopt", resource="default_config.yaml")
DEFAULT_CONFIG = yaml.full_load(default_config)


def test_reconcile_config_args_no_config(caplog) -> None:
    """Test the handling of config file function with no config."""
    args = argparse.Namespace(
        config_file=None,
    )
    config = reconcile_config_args(args=args, default_config=DEFAULT_CONFIG)

    # Check that the config passes the schema
    config.pop("config_file")
    with caplog.at_level(logging.INFO):
        validate_config(config, schema=LAYOPT_CONFIG_SCHEMA, config_type="default")

    assert "✅ The default configuration is valid." in caplog.text


@pytest.mark.parametrize(
    ("args", "parameter", "value"),
    [
        pytest.param(
            argparse.Namespace(config_file=None, stress_tensile=10.0),
            "stress_tensile",
            10.0,
            id="stress_tensile 10.0",
        ),
        pytest.param(
            argparse.Namespace(config_file=None, loaded_points=[[6, 2]]),
            "loaded_points",
            np.asarray([[6, 2]]),
            id="loaded_points [[6, 2]]",
        ),
        pytest.param(
            argparse.Namespace(config_file=None, filter_levels=[0.001, 0.01, 0.1]),
            "filter_levels",
            [0.001, 0.01, 0.1],
            id="filter_levels not None",
        ),
    ],
)
def test_reconcile_config_args(
    args: argparse.Namespace,
    parameter: str,
    value: float | npt.NDArray | bool,
) -> None:
    """Test that passing alternative ``args`` to ``reconcile_config_args()`` updates the configuration."""
    config: dict[str, Any] = reconcile_config_args(
        args=args, default_config=DEFAULT_CONFIG
    )
    if isinstance(config[parameter], np.ndarray):
        np.testing.assert_array_equal(config[parameter], value)
    else:
        assert config[parameter] == value


@pytest.mark.parametrize(
    ("args"),
    [
        pytest.param(
            argparse.Namespace(config_file=None, stress_tensile=-1.0),
            id="stress_tensile < 0.0",
        ),
        pytest.param(
            argparse.Namespace(config_file=None, loaded_points=[1, 2]),
            id="loaded_points 1 dimension",
        ),
        pytest.param(
            argparse.Namespace(config_file=None, filter_levels="yes"),
            id="filter_levels str not bool",
        ),
    ],
)
def test_reconcile_config_args_invalid_args(
    args: argparse.Namespace,
) -> None:
    """Test that providing invalid values for parameters raises Schema errors from ``reconcile_config_args()``."""
    config: dict[str, Any] = reconcile_config_args(
        args=args, default_config=DEFAULT_CONFIG
    )
    with pytest.raises(SchemaError):
        validate_config(config, schema=LAYOPT_CONFIG_SCHEMA, config_type="default")


@pytest.mark.parametrize(
    ("dict1", "dict2", "expected_merged_dict"),
    [
        pytest.param(
            {"a": 1, "b": 2},
            {"c": 3, "d": 4},
            {"a": 1, "b": 2, "c": 3, "d": 4},
            id="two dicts, no common keys",
        ),
        pytest.param(
            {"a": 1, "b": 2},
            {"b": 3, "c": 4},
            {"a": 1, "b": 3, "c": 4},
            id="two dicts, one common key, testing priority of second dict",
        ),
        # Nested dictionaries
        pytest.param(
            {"a": 1, "b": {"c": 2, "d": 3}},
            {"b": {"c": 4, "e": 5}},
            {"a": 1, "b": {"c": 4, "d": 3, "e": 5}},
            id="nested dictionaries, one common key in nested dict, testing priority of second dict",
        ),
    ],
)
def test_merge_mappings(
    dict1: dict[str, Any], dict2: dict[str, Any], expected_merged_dict: dict[str, Any]
) -> None:
    """Test ``merge_mappings()``."""
    merged_dict = merge_mappings(dict1, dict2)
    assert merged_dict == expected_merged_dict
