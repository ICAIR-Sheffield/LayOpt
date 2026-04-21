"""Test the config module functions."""

import argparse
from pathlib import Path
from pkgutil import get_data
from typing import Any

import pandas as pd
import pytest
import yaml

from layopt import io

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
    converted_path = io.convert_path(test_dir)

    assert isinstance(converted_path, Path)
    assert tmp_path == converted_path


def test_read_yaml() -> None:
    """Test reading of YAML files using ``read_yaml()``."""
    # Dummy config for testing 'read_yaml()'
    sample_config = io.read_yaml(RESOURCES / "test.yaml")
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
    io.write_config(args)
    if args.filename is None:
        assert Path(tmp_path / "default_config.yaml").exists()
    else:
        assert Path(tmp_path / args.filename).exists()


@pytest.mark.parametrize(
    ("results", "df"),
    [
        pytest.param(
            {"a": 1, "b": 3},
            pd.DataFrame({"a": [1], "b": [3]}),
            id="basic",
        ),
        pytest.param(
            {
                "timestamp": "2026-04-08 13:57:09",
                "problem_name": "short cantilever",
                "width": 3,
                "height": 6,
                "n_load_points": 1,
                "n_patterns_total": 2,
                "n_patterns_active": 1,
                "load_large": 50.0,
                "load_small": 5.0,
                "iterations": 2,
                "final_volume": 300.0000000000194,
                "n_members_final": 81,
                "n_nodes": 28,
                "n_ground_structure": 251,
                "cpu_time_setup": 0.00429152,
                "cpu_time_solve": 0.043679378000000005,
                "primal_method": "load_factor",
                "notes": "short cantilever test",
            },
            pd.DataFrame(
                {
                    "timestamp": ["2026-04-08 13:57:09"],
                    "problem_name": ["short cantilever"],
                    "width": [3],
                    "height": [6],
                    "n_load_points": [1],
                    "n_patterns_total": [2],
                    "n_patterns_active": [1],
                    "load_large": [50.0],
                    "load_small": [5.0],
                    "iterations": [2],
                    "final_volume": [300.0000000000194],
                    "n_members_final": [81],
                    "n_nodes": [28],
                    "n_ground_structure": [251],
                    "cpu_time_setup": [0.00429152],
                    "cpu_time_solve": [0.043679378000000005],
                    "primal_method": ["load_factor"],
                    "notes": ["short cantilever test"],
                },
            ),
            id="realistic",
        ),
    ],
)
def test_dict_to_df(results: dict[str, Any], df: pd.DataFrame, snapshot) -> None:
    """Test conversion of dictionary to data frame using ``io.dict_to_df()``."""
    df = io.dict_to_df(results=results)
    assert df.to_string() == snapshot
