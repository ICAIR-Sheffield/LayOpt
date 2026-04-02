"""Test the config module functions."""

import argparse
from pathlib import Path
from pkgutil import get_data

import pytest
import yaml

from layopt.io import (
    convert_path,
    read_yaml,
    write_config,
)

# from layopt.validation import DEFAULT_CONFIG_SCHEMA, validate_config

BASE_DIR = Path.cwd()
RESOURCES = BASE_DIR / "tests" / "resources"

default_config = get_data(package="layopt", resource="default_config.yaml")
DEFAULT_CONFIG = yaml.full_load(default_config)

CONFIG = {
    "this": "is",
    "a": "test",
    "yaml": "file",
    "numbers": 123,
    "logical": True,
    "nested": {"something": "else"},
    "a_list": [1, 2, 3],
}


def test_convert_path(tmp_path: Path) -> None:
    """Test ``convert_path()``."""
    test_dir = str(tmp_path)
    converted_path = convert_path(test_dir)

    assert isinstance(converted_path, Path)
    assert tmp_path == converted_path


def test_read_yaml() -> None:
    """Test reading of YAML files using ``read_yaml()``."""
    # Dummy config for testing 'read_yaml()'
    sample_config = read_yaml(RESOURCES / "test.yaml")
    assert sample_config == CONFIG


@pytest.mark.parametrize(
    ("args"),
    [
        pytest.param(argparse.Namespace(filename=None), id="no filename"),
        pytest.param(
            argparse.Namespace(filename="another_config.yaml"),
            id="alternative filename",
        ),
    ],
)
def test_write_config(args: argparse.Namespace, tmp_path: Path) -> None:
    """Test writing of YAML configuration file using ``write_config()``."""
    args.output_dir = tmp_path
    write_config(args)
    if args.filename is None:
        assert Path(tmp_path / "default_config.yaml").exists()
    else:
        assert Path(tmp_path / args.filename).exists()
