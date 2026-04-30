"""Tests for the entry_point module."""

import contextlib
import os
from collections.abc import Callable
from pathlib import Path

import pandas as pd
import pytest

from layopt import io, run_modules
from layopt.entry_point import entry_point

GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"


@pytest.mark.parametrize("option", ["-h", "--help"])
def test_entry_point_help(option: str, capsys) -> None:
    """Test help for the ``entry_point()`` function."""
    with contextlib.suppress(SystemExit):
        entry_point(manually_provided_args=[option])
    output = capsys.readouterr().out
    assert "usage:" in output
    assert "program" in output


@pytest.mark.parametrize(
    (("argument", "option")),
    [
        pytest.param("optimise", "-h", id="process with -h"),
        pytest.param("optimise", "--help", id="process with --help"),
        pytest.param("create-config", "-h", id="create-config with -h"),
        pytest.param("create-config", "--help", id="create-config with --help"),
    ],
)
def test_entry_point_subprocess_help(capsys, argument: str, option: str) -> None:
    """Test the help argument to the sub-entry points."""
    with contextlib.suppress(SystemExit):
        entry_point(manually_provided_args=[argument, option])
    output = capsys.readouterr().out
    assert "usage:" in output
    assert argument in output


@pytest.mark.parametrize(
    ("options", "expected_function", "expected_args"),
    [
        pytest.param(
            [
                "-c",
                "dummy/config/dir/config.yaml",
                "optimise",
            ],
            run_modules.optimise,
            {"config_file": Path("dummy/config/dir/config.yaml")},
            id="Optimise with config file argument",
        ),
        pytest.param(
            [
                "--output-dir",
                "/tmp/output/",
                "optimise",
            ],
            run_modules.optimise,
            {"output_dir": Path("/tmp/output")},
            id="Optimise with output (long) arguments",
        ),
        pytest.param(
            [
                "-l",
                "debug",
                "--cores",
                "16",
                "optimise",
            ],
            run_modules.optimise,
            {"log_level": "debug", "cores": 16},
            id="Optimise with log_level (short), cores (long)",
        ),
        pytest.param(
            [
                "create-config",
                "-f",
                "dummy_config_file.yaml",
            ],
            io.write_config,
            {"filename": Path("dummy_config_file.yaml")},
            id="Create config with custom filename",
        ),
        pytest.param(
            [
                "create-config",
                "-f",
                "dummy_config_file.yaml",
            ],
            io.write_config,
            {"filename": Path("dummy_config_file.yaml")},
            id="Create config with custom filename (short), custom module (long)",
        ),
    ],
)
def test_entry_points(
    options: list, expected_function: Callable, expected_args: dict
) -> None:
    """Ensure the correct function is called for each program, and arguments are carried through correctly."""
    returned_args = entry_point(options, testing=True)
    # convert argparse's Namespace object to dictionary
    returned_args_dict = vars(returned_args)
    # check that the correct function is collected
    assert returned_args.func == expected_function
    # check that the argument has successfully been passed through into the dictionary
    for argument, value in expected_args.items():
        assert returned_args_dict[argument] == value


# ns-rse 2026-04-14 - Tests `test_optimise()` is very similar to `test_run_modules.py::run_modules.optimise()`  as the
# former  is a wrapper calling the later


# pylint: disable=duplicate-code
@pytest.mark.skipif(
    GITHUB_ACTIONS,
    reason="mosek library requires license so test will always fail in continuous integration",
)
@pytest.mark.parametrize(
    ("manual_args"),
    [
        pytest.param(
            ["--log-level", "info", "optimise", "--width", "1", "--height", "1"],
            id="optimise 1x1 structure ",
        ),
    ],
)
def test_optimise(manual_args: list[str], tmp_path: Path, snapshot) -> None:
    """Test for ``run_modules.optimise()``."""
    manual_args = ["--output-dir", str(tmp_path), *manual_args]
    entry_point(manually_provided_args=manual_args)
    # Check there are two files in the output directory
    assert sum(1 for _ in tmp_path.iterdir() if _.is_file()) == 2
    # Load csv file and check against snapshot
    csv_out = list(tmp_path.glob("*.csv"))
    csv_results = pd.read_csv(csv_out[0])
    assert (
        csv_results.drop(
            ["timestamp", "cpu_time_setup", "cpu_time_solve"], axis=1
        ).to_string()
        == snapshot
    )
