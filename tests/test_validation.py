"""Test validation function."""

from contextlib import nullcontext as does_not_raise
from pathlib import Path
from pkgutil import get_data

import pytest
import yaml
from schema import Or, Schema, SchemaError

from layopt.validation import DEFAULT_CONFIG_SCHEMA, validate_config

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
    ("config", "expectation"),
    [
        # A valid configuration
        (
            {"a": Path(), "b": "aa", "positive_integer": 4, "absolute_threshold": 10.0},
            does_not_raise(),
        ),
        # Invalid value for a (string instead of Path)
        (
            {"a": "path", "b": "aa", "positive_integer": 4, "absolute_threshold": 10.0},
            pytest.raises(SchemaError),
        ),
        # Invalid value for b (int instead of str)
        (
            {"a": Path(), "b": 3, "positive_integer": 4, "absolute_threshold": 10.0},
            pytest.raises(SchemaError),
        ),
        # Invalid value for positive_integer (-ve instead +ve)
        (
            {"a": Path(), "b": 3, "positive_integer": -4, "absolute_threshold": 10.0},
            pytest.raises(SchemaError),
        ),
        # Invalid value for absolute_threshold (str instead of int/float)
        (
            {"a": Path(), "b": 3, "positive_integer": -4, "absolute_threshold": "five"},
            pytest.raises(SchemaError),
        ),
    ],
)
def test_validate(config, expectation) -> None:
    """Test various configurations."""
    with expectation:
        validate_config(config, schema=TEST_SCHEMA, config_type="Test YAML")


@pytest.mark.xfail(
    reason=(
        "Need to run config.update_config() to convert str > Path and others "
        "tested by tests_config.py::test_reoncile_config_args_no_config() and "
        "tests_config.py::test_reconcile_config_args_invalid_args()."
    )
)
def test_validate_default_config(caplog) -> None:
    """Test that the ``default_config.yaml`` validates against the schema."""
    default_config = get_data(package="layopt", resource="default_config.yaml")
    default_config = yaml.full_load(default_config)
    with does_not_raise():
        validate_config(
            default_config,
            schema=DEFAULT_CONFIG_SCHEMA,
            config_type="default",
        )
    assert "The default configuration is valid" in caplog.text
