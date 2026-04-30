"""Test validation function."""

from contextlib import nullcontext as does_not_raise
from pathlib import Path
from pkgutil import get_data
from typing import Any

import pytest
import yaml
from schema import Or, Schema, SchemaError

from layopt import config
from layopt.validation import LAYOPT_CONFIG_SCHEMA, validate_config

TEST_SCHEMA = Schema(
    {
        "a": Path,
        "b": Or(
            "aa", "bb", error="Invalid value in config, valid values are 'aa' or 'bb"
        ),
        "positive_integer": lambda n: n > 0,
        "absolute_threshold": Or(
            int, float, error="Invalid value in config should be type int or float"
        ),
    }
)


@pytest.mark.parametrize(
    ("new_config", "schema", "expectation"),
    [
        pytest.param(
            {"a": Path(), "b": "aa", "positive_integer": 4, "absolute_threshold": 10.0},
            TEST_SCHEMA,
            does_not_raise(),
            id="valid configuration",
        ),
        pytest.param(
            {"a": "path", "b": "aa", "positive_integer": 4, "absolute_threshold": 10.0},
            TEST_SCHEMA,
            pytest.raises(SchemaError),
            id="Invalid value for a (string instead of Path)",
        ),
        pytest.param(
            {"a": Path(), "b": 3, "positive_integer": 4, "absolute_threshold": 10.0},
            TEST_SCHEMA,
            pytest.raises(SchemaError),
            id="Invalid value for b (int instead of str)",
        ),
        pytest.param(
            {"a": Path(), "b": 3, "positive_integer": -4, "absolute_threshold": 10.0},
            TEST_SCHEMA,
            pytest.raises(SchemaError),
            id="Invalid value for positive_integer (-ve instead +ve)",
        ),
        pytest.param(
            {"a": Path(), "b": 3, "positive_integer": -4, "absolute_threshold": "five"},
            TEST_SCHEMA,
            pytest.raises(SchemaError),
            id="Invalid value for absolute_threshold (str instead of int/float)",
        ),
        pytest.param(
            {"primal_method": "nonsense"},
            LAYOPT_CONFIG_SCHEMA,
            pytest.raises(SchemaError),
            id="Invalid value for primal_method",
        ),
    ],
)
def test_validate_config_exceptions(
    new_config: dict[str, Any], schema: dict[str, Any], expectation
) -> None:
    """Test various configurations."""
    if "primal_method" in new_config:
        default_config = get_data(package="layopt", resource="default_config.yaml")
        default_config = yaml.full_load(default_config)
        for key, value in new_config.items():
            default_config[key] = value
        # Have to convert to numpy arrays
        for to_convert in ["loaded_points", "support_points", "filter_levels"]:
            default_config = config._convert_to_numpy_array(  # pylint: disable=protected-access
                config=default_config, to_convert=to_convert
            )
        new_config = default_config
    with expectation:
        validate_config(new_config, schema=schema, config_type="Test YAML")


@pytest.mark.parametrize(
    ("options", "expectation"),
    [
        pytest.param(
            {"primal_method": None},
            does_not_raise(),
            id="primal_method None",
        ),
        pytest.param(
            {"primal_method": "residual"},
            does_not_raise(),
            id="primal_method residual",
        ),
        pytest.param(
            {"primal_method": "load_factor"},
            does_not_raise(),
            id="primal_method load_factor",
        ),
    ],
)
def test_validate_config_valid(
    options: dict[str, Any] | None, expectation, caplog
) -> None:
    """Test that the ``default_config.yaml`` with variations validates against the ``LAYOPT_CONFIG_SCHEMA``."""
    default_config = get_data(package="layopt", resource="default_config.yaml")
    default_config = yaml.full_load(default_config)
    if options is not None:
        for key, value in options.items():
            default_config[key] = value
    # Have to convert to numpy arrays
    for to_convert in ["loaded_points", "support_points", "filter_levels"]:
        default_config = config._convert_to_numpy_array(  # pylint: disable=protected-access
            config=default_config, to_convert=to_convert
        )
    with expectation:
        validate_config(
            default_config,
            schema=LAYOPT_CONFIG_SCHEMA,
            config_type="default configuration",
        )
    assert "The default configuration is valid" in caplog.text
