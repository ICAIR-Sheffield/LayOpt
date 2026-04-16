"""Tests of the run_modules module."""

import argparse
import os
from pathlib import Path

import pandas as pd
import pytest

from layopt import LAYOPT_BASE_VERSION, run_modules

GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"

# ns-rse 2026-04-14 - Tests `run_modules.optimise()` is very similar to `tests_entry_point.py::test_optimise()` as the
# later is a wrapper calling the former


# pylint: disable=duplicate-code
@pytest.mark.skipif(
    GITHUB_ACTIONS,
    reason="mosek library requires license so test will always fail in continuous integration",
)
@pytest.mark.parametrize(
    ("args", "result_files"),
    [
        pytest.param(
            argparse.Namespace(
                config_file=None,
                width=1,
                height=1,
                log_level="info",
                func="optimise",
                module="layopt",
            ),
            2,
            id="1x1",
        ),
        pytest.param(
            argparse.Namespace(
                config_file=None,
                width=2,
                height=2,
                log_level="info",
                func="optimise",
                module="layopt",
            ),
            2,
            id="2x2",
        ),
    ],
)
def test_optimise(
    args: argparse.Namespace, result_files: int, tmp_path: Path, snapshot
) -> None:
    """Test the ``optimse()`` function directly."""
    args.output_dir = tmp_path
    run_modules.optimise(args=args)
    # Check there are two files in the output directory
    assert sum(1 for _ in tmp_path.iterdir() if _.is_file()) == result_files
    # Load csv file and check against snapshot
    csv_out = list(tmp_path.glob("*.csv"))
    csv_results = pd.read_csv(csv_out[0])
    assert (
        csv_results.drop(
            ["timestamp", "cpu_time_setup", "cpu_time_solve"], axis=1
        ).to_string()
        == snapshot
    )


@pytest.mark.parametrize(
    ("_config", "check"),
    [
        pytest.param(
            {"output_dir": Path("tmp"), "csv_filename": "just_a_test.csv"},
            "tmp/just_a_test.csv",
            id="dummy output_dir and filename",
        )
    ],
)
def test_completion_message(_config: dict, check: str, caplog) -> None:
    """Test the ``completion_message()`` correctly parses the ``_config()`` argument."""
    run_modules.completion_message(_config=_config)
    assert check in caplog.text
    assert "ICAIR-Sheffield.github.io/LayOpt" in caplog.text
    assert LAYOPT_BASE_VERSION in caplog.text
