"""Tests for the entry_point module."""

from collections.abc import Callable
from pathlib import Path

import pytest

from layopt import io, run_modules
from layopt.entry_point import entry_point


@pytest.mark.parametrize("option", ["-h", "--help"])
def test_entry_point_help(option: str, capsys) -> None:
    """Test help for the ``entry_point()`` function."""
    try:
        entry_point(manually_provided_args=[option])
    except SystemExit:
        pass
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
    try:
        entry_point(manually_provided_args=[argument, option])
    except SystemExit:
        pass
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
                "-b",
                "/tmp/",
                "--output-dir",
                "/tmp/output/",
                "optimise",
            ],
            run_modules.optimise,
            {"base_dir": Path("/tmp/"), "output_dir": Path("/tmp/output")},
            id="Optimise with base dir (short) and output (long) arguments",
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
                "--module",
                "afmslicer",
            ],
            io.write_config,
            {"filename": Path("dummy_config_file.yaml"), "module": "afmslicer"},
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
