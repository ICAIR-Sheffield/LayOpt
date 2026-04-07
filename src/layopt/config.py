"""Module functions for working with configuration files."""

from __future__ import annotations

from argparse import Namespace  # noqa: TC003
from collections.abc import MutableMapping
from pprint import pformat
from typing import Any

import numpy as np
from loguru import logger

from layopt.io import convert_path, read_yaml


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
        Command line arguments passed into TopoStats.
    default_config : dict[str, Any]
        Dictionary containing the default configuration for the package.

    Returns
    -------
    dict[str, Any]
        The configuration dictionary.
    """
    # If we have args check for 'config_file', if present load and merge with default
    if args is not None and args.config_file is not None:
        config = read_yaml(str(args.config_file))
        config = merge_mappings(map1=default_config, map2=config)
    # If no args we use the default_config
    else:
        config = default_config
    # Override the config with command line arguments
    if args is not None:
        config = merge_mappings(map1=config, map2=vars(args))
    logger.debug(f"\nConfiguration after update : \n{pformat(config, indent=4)}\n")
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
        else:
            map1[key] = value
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
    return dict(map1)
