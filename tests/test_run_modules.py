"""Tests of the run_modules module."""

import argparse
import os
from pathlib import Path
from typing import Any

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
    """Test the ``optimise()`` function directly."""
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
    ("args", "log_string"),
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
            "INFO",
            id="no config; log-level info",
        ),
        pytest.param(
            argparse.Namespace(
                config_file=None,
                width=1,
                height=1,
                log_level="debug",
                func="optimise",
                module="layopt",
            ),
            "DEBUG",
            id="no config; log-level debug",
        ),
        pytest.param(
            argparse.Namespace(
                config_file=Path("tests/resources/config/info_config.yaml"),
                width=1,
                height=1,
                log_level="error",
                func="optimise",
                module="layopt",
            ),
            "ERROR",
            id="config info; log-level error",
        ),
        pytest.param(
            argparse.Namespace(
                config_file=Path("tests/resources/config/debug_config.yaml"),
                width=1,
                height=1,
                log_level="info",
                func="optimise",
                module="layopt",
            ),
            "INFO",
            id="config debug; log-level info",
        ),
    ],
)
def test_optimise_different_log_levels(
    args: argparse.Namespace, log_string: str, tmp_path: Path, capsys
) -> None:
    """
    Test parsing of arguments from both configuration file and from the command line.

    This is a slightly indirect test because it is 'run_modules._parse_configuration()' and in turn
    'config.reconcile_config_args()' that do the leg work here but this is still a useful test as it emulates what
    happens when the entry point is called.

    Note we do not use the Pytest 'caplog' because it defaults to the standard library's 'logging' module which doesn't
    play well with 'loguru'. Instead we capture logging via 'capsys'.
    """
    args.output_dir = tmp_path
    run_modules.optimise(args=args)
    output = capsys.readouterr().err
    assert log_string in output


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
def test_completion_message(_config: dict[str, Any], check: str, caplog) -> None:
    """Test the ``completion_message()`` correctly parses the ``_config()`` argument."""
    run_modules.completion_message(_config=_config)
    assert check in caplog.text
    assert "ICAIR-Sheffield.github.io/LayOpt" in caplog.text
    assert LAYOPT_BASE_VERSION in caplog.text
