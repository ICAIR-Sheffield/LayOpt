"""Module functions for working with configuration files."""

from __future__ import annotations

from argparse import Namespace  # noqa: TC003
from collections.abc import MutableMapping
from pathlib import Path
from pprint import pformat
from typing import Any

import numpy as np
from loguru import logger

from layopt.io import convert_path, get_date_time, read_yaml


def reconcile_config_args(
    args: Namespace | None, default_config: dict[str, Any]
) -> dict[str, Any]:
    """
    Reconcile command line arguments with the default configuration.

    Command line arguments take precedence over the default configuration. If a partial configuration file is specified
    (with '-c' or '--config-file') the defaults are over-ridden by these values (internally the configuration
    dictionary is updated with these values). Any other command line arguments take precedence over both the default and
    those supplied in a configuration file (again the dictionary is updated).

    The final configuration is validated before processing begins.

    Parameters
    ----------
    args : Namespace
        Command line arguments passed into LayOpt.
    default_config : dict[str, Any]
        Dictionary containing the default configuration for the package.

    Returns
    -------
    dict[str, Any]
        The configuration dictionary.
    """
    # If we have args check for 'config_file', if present load and merge with default_config
    if args is not None and args.config_file is not None:
        logger.debug(
            f"BEFORE update with config_file args :\n{pformat(vars(args), indent=4)}"
        )
        logger.debug(
            f"BEFORE update with config_file default_config :\n{pformat(default_config, indent=4)}"
        )
        config = read_yaml(str(args.config_file))
        config = merge_mappings(map1=default_config, map2=config)
    # If no args we use the default_config
    else:
        config = default_config
    # Override the config with command line arguments
    if args is not None:
        _args = vars(args)
        # Remove args that are not part of the configuration
        _args.pop("config_file")
        _args.pop("func")
        _args.pop("module")
        logger.debug(
            f"BEFORE update from command line args :\n{pformat(_args, indent=4)}"
        )
        logger.debug(
            f"BEFORE update from command line config :\n{pformat(default_config, indent=4)}"
        )
        config = merge_mappings(map1=config, map2=_args)
    logger.debug(f"Final configuration AFTER update : \n{pformat(config, indent=4)}\n")
    return dict(config)


def merge_mappings(map1: MutableMapping, map2: MutableMapping) -> dict[str, Any]:
    """
    Merge two mappings (dictionaries), with priority given to the second mapping.

    ``map1`` is updated with values from ``map2``.

    Parameters
    ----------
    map1 : MutableMapping
        First mapping to merge, with secondary priority.
    map2 : MutableMapping
        Second mapping to merge, with primary priority.

    Returns
    -------
    dict
        Merged dictionary.
    """
    for key, value in map2.items():
        # Recurse if we have a MutableMapping (e.g. nested dictionary)
        if isinstance(value, MutableMapping):
            map1[key] = merge_mappings(map1.get(key, {}), value)
        # Otherwise update the value
        elif value is not None:
            logger.debug(f"key  : {key=}")
            map1[key] = value
            logger.debug(f"map1 : {map1[key]=}")
            logger.debug(f"map2 : {value=}")
    # Tidy up variables
    if "base_dir" in map1:
        map1["base_dir"] = (
            Path("./") if map1["base_dir"] is None else convert_path(map1["base_dir"])
        )
    if "output_dir" in map1:
        map1["output_dir"] = convert_path(map1["output_dir"])
    if "load_direction" in map1:
        map1["load_direction"] = (
            map1["load_direction"][0],
            map1["load_direction"][1],
        )
    # Convert to numpy arrays
    if "loaded_points" in map1:
        map1["loaded_points"] = np.asarray(map1["loaded_points"])
    if "support_points" in map1:
        map1["support_points"] = np.asarray(map1["support_points"])
    if "filter_levels" in map1:
        map1["filter_levels"] = np.asarray(map1["filter_levels"])
    if "csv_filename" in map1 and map1["csv_filename"] == "results.csv":
        map1["csv_filename"] = (
            f"results_{get_date_time(strftime='%Y-%m-%d-%H%M%S')}.csv"
        )
    return dict(map1)
