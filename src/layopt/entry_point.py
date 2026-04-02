"""Argument parsing and entry point for command line usage."""

from __future__ import annotations

import argparse as arg
import sys
from pathlib import Path
from typing import Any

from layopt import (
    __version__,  # , run_modules
)
from layopt.io import write_config


def layopt_parser() -> arg.ArgumentParser:
    """
    Create a parser for reading options at the commandline.

    The parser has multiple sub-parsers for reading options to run ``layopt``.

    Returns
    -------
    arg.ArgumentParser
        Argument parser.
    """
    parser = arg.ArgumentParser(description="Run layopt.")
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"Installed version of Layopt: {__version__}",
        help="Report the current version of Layopt that is installed",
    )
    parser.add_argument(
        "-c",
        "--config-file",
        dest="config_file",
        type=Path,
        required=False,
        help="Path to a YAML configuration file.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        dest="output_dir",
        type=Path,
        required=False,
        help="Output directory to write results to.",
    )
    parser.add_argument(
        "-l",
        "--log-level",
        dest="log_level",
        type=str,
        required=False,
        help="Set verbosity of logging.",
    )
    parser.add_argument(
        "-j",
        "--cores",
        dest="cores",
        required=False,
        help="Number of cores to use for parallel processing.",
    )
    # Add subparsers
    subparsers = parser.add_subparsers(
        title="program",
        description="Available processing options are :",
        dest="module",
    )

    # Add an optomise parser
    optimise_parser = subparsers.add_parser(
        "optimise",
        description="Run Layopt",
        help="Run LayOpt",
    )
    optimise_parser.add_argument(
        "--width",
        dest="width",
        type=int,
        required=False,
        help="Width of structure.",
    )
    optimise_parser.add_argument(
        "--height",
        dest="height",
        type=int,
        required=False,
        help="Height of structure.",
    )
    optimise_parser.add_argument(
        "--stress-tensile",
        dest="stress_tensile",
        type=float,
        required=False,
        help="Tensile stress.",
    )
    optimise_parser.add_argument(
        "--stress-compressive",
        dest="stress_compressive",
        type=float,
        required=False,
        help="Compressive stress.",
    )
    optimise_parser.add_argument(
        "--joint-cost",
        dest="joint_cost",
        type=float,
        required=False,
        help="Joint cost.",
    )
    optimise_parser.add_argument(
        "--load-direction",
        dest="load_direction",
        nargs="+",
        type=int,
        required=False,
        help="Load direction.",
    )
    optimise_parser.add_argument(
        "--load-large",
        dest="load_large",
        type=float,
        required=False,
        help="Load large.",
    )
    optimise_parser.add_argument(
        "--load-small",
        dest="load_small",
        type=float,
        required=False,
        help="Load small.",
    )
    optimise_parser.add_argument(
        "--max-length",
        dest="max_length",
        type=float,
        required=False,
        help="Max length.",
    )
    optimise_parser.add_argument(
        "--member-area-filtering",
        dest="member_area_filtering",
        type=bool,
        required=False,
        help="Member area filtering.",
    )
    optimise_parser.add_argument(
        "--primal-method",
        dest="primal_method",
        type=str,
        required=False,
        help="Primal method.",
    )
    optimise_parser.add_argument(
        "--problem-name",
        dest="problem_name",
        type=str,
        required=False,
        help="Problem name",
    )
    optimise_parser.add_argument(
        "--save-to-csv",
        dest="save_to_csv",
        type=bool,
        required=False,
        help="Whether to save output to '.csv' file.",
    )
    optimise_parser.add_argument(
        "--notes", dest="notes", type=str, required=False, help="Additional notes."
    )
    # optimise_parser.set_defaults(func=run_modules.optimise)

    # Add a create configuration parser
    create_config_parser = subparsers.add_parser(
        "create-config",
        description="Create a configuration file using the defaults.",
        help="Create a configuration file using the defaults.",
    )
    create_config_parser.add_argument(
        "-f",
        "--filename",
        dest="filename",
        type=Path,
        required=False,
        help="Name of YAML file to save configuration to (default 'config.yaml').",
    )
    create_config_parser.add_argument(
        "-o",
        "--output-dir",
        dest="output_dir",
        type=Path,
        required=False,
        default="./",
        help="Path to where the YAML file should be saved (default './' the current directory).",
    )
    create_config_parser.add_argument(
        "-m",
        "--module",
        dest="module",
        default="afmslicer",
        help="The AFM module to use, currently `afmslicer` (default).",
    )
    create_config_parser.add_argument(
        "-c",
        "--config",
        dest="config",
        type=str,
        default="default",
        help="Configuration to use, currently only 'default' is supported.",
    )
    create_config_parser.set_defaults(func=write_config)

    return parser


def entry_point(
    manually_provided_args: list[Any] | None = None, testing: bool = False
) -> None | arg.Namespace:
    """
    Entry point for all LayOpt programs.

    Main entry point for running ``layopt`` which allows the different processing, plotting and testing modules to be
    run.

    Parameters
    ----------
    manually_provided_args : None
        Manually provided arguments.
    testing : bool
        Whether testing is being carried out.

    Returns
    -------
    None
        Function does not return anything.
    """
    # Create LayOpt parser
    parser = layopt_parser()
    args = (
        parser.parse_args()
        if manually_provided_args is None
        else parser.parse_args(manually_provided_args)
    )
    # If no module has been specified print help and exit
    if not args.module:
        parser.print_help()
        sys.exit()
    if testing:
        return args
    # Run the specified module(s)
    args.func(args)
    return None
