"""Run different layopt modules."""

import argparse
import sys
from pathlib import Path
from pkgutil import get_data
from pprint import pformat
from typing import Any

import numpy as np
from art import tprint
from loguru import logger
from ruamel.yaml import YAML

from layopt import (
    CONFIG_DOCUMENTATION_REFERENCE,
    LAYOPT_BASE_VERSION,
    LAYOPT_COMMIT,
    classes,
    config,
    io,
    layopt,
    validation,
)

HEADER_MESSAGE = f"# Configuration from LayOpt run complete : {io.get_date_time()}\n{CONFIG_DOCUMENTATION_REFERENCE}"


def _log_setup(_config: dict[str, Any]) -> None:
    """
    Log the current configuration.

    Parameters
    ----------
    _config : dict
        Dictionary of configuration options.
    """
    logger.info(f"Width                               : {_config['width']}")
    logger.info(f"Height                              : {_config['height']}")
    logger.info(f"Load (Large)                        : {_config['load_large']}")
    logger.info(f"Load (Small)                        : {_config['load_small']}")
    logger.info(f"Max Length                          : {_config['max_length']}")
    logger.info(
        f"Stress (Compressive)                : {_config['stress_compressive']}"
    )
    logger.info(f"Stress (Tensile)                    : {_config['stress_tensile']}")
    logger.info(f"CVXPY solver                        : {_config['cvxpy']['solver']}")
    logger.info(f"Output directory                    : {_config['output_dir']}")
    logger.info(f"Cores for parallel processing       : {_config['cores']}")


def _set_logging(log_level: str) -> None:
    """
    Set up loguru logging.

    Parameters
    ----------
    log_level : str
        Logging level.
    """
    logger.remove()
    logger.add(sys.stderr, level=log_level.upper())


def _parse_configuration(args: argparse.Namespace | None = None) -> classes.Parameters:
    """
    Load configurations, validate and check run steps are consistent.

    Parameters
    ----------
    args : argparse.Namespace, optional
        Arguments.

    Returns
    -------
    dict[str, Any]
        Returns the dictionary of configuration options, updated with missing values from default and command line
        options taking precedence.
    """
    # Parse command line options, load config (or default) and update with command line options
    if args.config_file is None:  # type: ignore[union-attr]
        default_config = get_data(
            package=layopt.__package__, resource="default_config.yaml"
        )
        yaml = YAML(typ="safe")
        default_config = yaml.load(default_config)
    else:
        logger.info(f"Loading configuration from : {args.config_file!s}")  # type: ignore[union-attr]
        with args.config_file.open(encoding="utf-8") as conf:  # type: ignore[union-attr]
            yaml = YAML(typ="safe")
            default_config = yaml.load(conf)
    _config = config.reconcile_config_args(args=args, default_config=default_config)
    # Validate configuration
    logger.debug(f"Configuration prior to validation :\n{pformat(_config, indent=4)}")
    validation.validate_config(
        _config,
        schema=validation.LAYOPT_CONFIG_SCHEMA,
        config_type="YAML configuration file",
    )
    # Set logging level
    _set_logging(log_level=_config["log_level"].upper())
    # Create base output directory
    _config["output_dir"].mkdir(parents=True, exist_ok=True)
    _log_setup(_config=_config)
    return classes.Parameters(**_config)


def optimise(args: argparse.Namespace | None = None) -> None:
    """
    Run optimisation.

    Parameters
    ----------
    args : argparse.Namespace | None
        Command line arguments for modifying configuration.
    """
    _set_logging(log_level=args.log_level)  # type: ignore[union-attr]
    logger.debug(f"\n{pformat(vars(args))}\n")
    _config = _parse_configuration(args)
    _set_logging(log_level=_config.log_level)
    # Ensure filter_levels is a list and includes 1.0
    filter_levels = (
        np.asarray([1.0])
        if len(_config.filter_levels) == 0
        else np.asarray(_config.filter_levels)
    )
    # ns-rse 2026-04-30 : if 1.0 isn't in filter_levels we add it so we always have unfiltered results
    if 1.0 not in filter_levels:
        # if 1.0 not in filter_levels:
        filter_levels = np.append(filter_levels, 1.0)
    _, _, results_df, _ = layopt.trussopt(parameters=_config)  # type: ignore[misc]
    # Transpose and tidy data frame and write results and configuration to disk
    results_df = results_df.T.reset_index(drop=True)
    results_df = results_df.sort_values(["filter_level"])
    results_df.to_csv(Path(_config.output_dir) / _config.csv_filename, index=False)
    io.write_config(_config)
    logger.info(f"Results saved to {Path(_config.output_dir) / _config.csv_filename}")
    completion_message(_config=_config)


def completion_message(_config: dict[str, Any] | classes.Parameters) -> None:
    """
    Print a completion message summarising images processed.

    Parameters
    ----------
    _config : dict[str, Any] | classes.Parameters
        Configuration dictionary.
    """
    output_dir = (
        _config["output_dir"] if isinstance(_config, dict) else _config.output_dir
    )
    csv_filename = (
        _config["csv_filename"] if isinstance(_config, dict) else _config.csv_filename
    )
    logger.info(
        "\n\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n"
    )
    tprint("LayOpt", font="twisted")
    logger.info(
        f"\n\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ COMPLETE ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n"
        f"  LayOpt Version              : {LAYOPT_BASE_VERSION}\n"
        f"  LayOpt Commit               : {LAYOPT_COMMIT}\n"
        f"  All statistics              : {output_dir!s}/{csv_filename}\n"
        f"  Configuration               : {output_dir!s}/"
        f"config_{io.get_date_time(strftime='%Y-%m-%d-%H%M%S')}.yaml\n\n"
        # f"  Email                       : layopt@sheffield.ac.uk\n"
        f"  Documentation               : https://ICAIR-Sheffield.github.io/LayOpt/\n"
        f"  Source Code                 : https://github.com/ICAIR-Sheffield/LayOpt/\n"
        f"  Bug Reports/Feature Request : https://github.com/ICAIR-Sheffield/LayOpt/issues/new/choose\n"
        f"  Citation File Format        : https://github.com/ICAIR-Sheffield/LayOpt/blob/main/CITATION.cff\n\n"
        f"  If you encounter bugs/issues or have feature requests please report them at the above URL\n"
        f"  or email us.\n\n"
        f"  If you have found LayOpt useful please consider citing it. A Citation File Format is\n"
        f"  linked above and available from the Source Code page.\n"
        f"~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n"
    )
