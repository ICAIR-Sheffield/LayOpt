"""Run different layopt modules."""

import argparse
import sys
from collections import defaultdict
from functools import partial
from multiprocessing import Pool
from pkgutil import get_data
from pprint import pformat
from typing import Any

import pandas as pd
import yaml
from art import tprint
from loguru import logger
from tqdm import tqdm

from layopt import (
    CONFIG_DOCUMENTATION_REFERENCE,
    LAYOPT_BASE_VERSION,
    LAYOPT_COMMIT,
    config,
    io,
    layopt,
    validation,
)

HEADER_MESSAGE = f"# Configuration from LayOpt run complete : {io.get_date_time()}\n{CONFIG_DOCUMENTATION_REFERENCE}"


def _log_setup(_config: dict) -> None:
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
    logger.info(f"Output directory                    : {_config['output_dir']}")
    logger.info(f"Cores for parallel processing       : {_config['cores']}")


def _set_logging(log_level: str | None) -> None:
    """
    Set up loguru logging.

    Parameters
    ----------
    log_level : str
        Logging level.
    """
    logger.remove()
    logger.add(sys.stderr, level=log_level.upper())


def _parse_configuration(args: argparse.Namespace | None = None) -> dict[str, Any]:
    """
    Load configurations, validate and check run steps are consistent.

    Parameters
    ----------
    args : argparse.Namespace | None
        Arguments.

    Returns
    -------
    dict[str, Any]
        Returns the dictionary of configuration options, updated with missing values from default and command line
        options taking precedence.
    """
    # Parse command line options, load config (or default) and update with command line options
    if args.config_file is None:
        default_config = get_data(
            package=layopt.__package__, resource="default_config.yaml"
        )
        default_config = yaml.full_load(default_config)
    else:
        logger.info(f"Loading configuration from : {args.config_file!s}")
        with args.config_file.open(encoding="utf-8") as conf:
            default_config = yaml.full_load(conf)
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
    return _config


def optimise(args: argparse.Namespace | None = None) -> None:
    """
    Run optimisation.

    Parameters
    ----------
    args : argparse.Namespace | None
        Command line arguments for modifying configuration.
    """
    _set_logging(log_level=args.log_level)
    logger.debug(f"\n{pformat(vars(args))}\n")
    _config = _parse_configuration(args)
    _set_logging(log_level=_config["log_level"])
    processing_function = partial(
        layopt.trussopt,
        # Placeholder,  # filter_levels
        width=_config["width"],
        height=_config["height"],
        stress_tensile=_config["stress_tensile"],
        stress_compressive=_config["stress_compressive"],
        joint_cost=_config["joint_cost"],
        loaded_points=_config["loaded_points"],
        load_direction=_config["load_direction"],
        load_large=_config["load_large"],
        load_small=_config["load_small"],
        max_length=_config["max_length"],
        support_points=_config["support_points"],
        # filter_levels=_config["filter_levels"],
        primal_method=_config["primal_method"],
        problem_name=_config["problem_name"],
        # save_to_csv=_config["save_to_csv"],
        notes=_config["notes"],
    )
    _config["filter_levels"] = [0.001, 0.01, 0.1]
    # Run processing in parallel
    with Pool(processes=_config["cores"]) as pool:
        all_results = defaultdict()
        with tqdm(
            total=len(_config["filter_levels"]),
            desc=f"Solving optimisation results are under '{_config['output_dir']}'.",
        ) as pbar:
            for _, _, result, filter_level in pool.imap_unordered(
                processing_function, _config["filter_levels"]
            ):
                if result is not None:
                    all_results[filter_level] = result
                pbar.update()
            logger.info("Optimisation complete.📈📉✅")
    # Aggregate results into a single data frame and write output
    all_results_df = pd.concat(all_results.values())
    all_results_df = all_results_df.sort_values(["filter_level"])
    all_results_df.to_csv(_config["output_dir"] / _config["csv_filename"], index=False)
    io.write_config(_config)
    logger.info(f"Results saved to {_config['output_dir'] / _config['csv_filename']}")
    completion_message(_config=_config)
    # ToDo - Add an output message summarising what has been run using art()


def completion_message(_config: dict) -> None:
    """
    Print a completion message summarising images processed.

    Parameters
    ----------
    _config : dict
        Configuration dictionary.
    """
    logger.info(
        "\n\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n"
    )
    tprint("LayOpt", font="twisted")
    logger.info(
        f"\n\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ COMPLETE ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n"
        f"  LayOpt Version              : {LAYOPT_BASE_VERSION}\n"
        f"  LayOpt Commit               : {LAYOPT_COMMIT}\n"
        f"  All statistics              : {_config['output_dir']!s}/{_config['csv_filename']}\n"
        f"  Configuration               : {_config['output_dir']}/"
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
