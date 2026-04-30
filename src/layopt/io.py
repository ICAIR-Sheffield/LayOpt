"""Module functions for working with configuration files."""

from __future__ import annotations

from argparse import Namespace
from datetime import datetime
from pathlib import Path
from pkgutil import get_data
from typing import Any

import numpy as np
import pandas as pd
import ruamel.yaml
import yaml
from loguru import logger
from yaml import YAMLError

from layopt import CONFIG_DOCUMENTATION_REFERENCE


def write_config(args: Namespace | dict[str, Any] | None) -> None:
    """
    Write a configuration file to YAML.

    Parameters
    ----------
    args : Namespace | dict[str, Any], optional
        A Namespace object parsed from argparse. If there are values for ``output_dir`` and ``filename`` these will be
        used to construct the path and filename to write the YAML file to.  If not then output files are contingent on
        how the function is being called. If it is from ``layopt create_config`` then ``default_config.yaml`` will be
        written. If it is at the end of processing then ``config_YY-MM-DD-hhmmss.yaml`` will be used.
    """
    # If args is `Namespace` then we are writing config with 'layopt create_config' subcommand
    if isinstance(args, Namespace):
        output_dir = Path("./") if args.output_dir is None else Path(args.output_dir)
        filename = "default_config.yaml" if args.filename is None else args.filename
        try:
            default_config = get_data(package="layopt", resource="default_config.yaml")
            config = yaml.full_load(default_config)
        except FileNotFoundError as exc:
            msg = "There was a problem loading 'default_config.yaml' try reinstalling LayOpt."
            raise (FileNotFoundError(msg)) from exc
    # Otherwise we are writing after 'layopt optimise' and config is a dictionary, this won't have a 'filename'
    # key/value pair
    elif isinstance(args, dict):
        output_dir = (
            Path("./") if args["output_dir"] is None else Path(args["output_dir"])
        )
        # Add missing 'filename' key/value pair
        filename = f"config_{get_date_time(strftime='%Y-%m-%d-%H%M%S')}.yaml"
        config = args
    else:
        msg = f"args is neither 'Namespace' or 'dict' : {type(args)}"
        raise TypeError(msg)
    if ".yaml" not in str(filename) and ".yml" not in str(filename):
        config_path = output_dir / f"{filename}.yaml"
    else:
        config_path = output_dir / filename
    logger_msg = "A sample configuration has been written to"
    with config_path.open("w", encoding="utf-8") as f:
        try:
            f.write(f"# Config generated {get_date_time()}\n")
            f.write(f"{CONFIG_DOCUMENTATION_REFERENCE}")
            yaml_out = ruamel.yaml.YAML()
            yaml_out.indent(sequence=4, offset=2)
            yaml_out.dump(dict_to_yaml(config), f)
            logger.info(f"{logger_msg} : {config_path!s}")
        except:  # noqa: E722, pylint: disable=W0702
            logger.error(f"Failed to write config to : {config_path}")


def dict_to_yaml(obj: Any) -> Any:
    """
    Clean a dictionary to basic data types for writing to YAML.

    Parameters
    ----------
    obj : Any
        An object for converting to basic data types.

    Returns
    -------
    Any
        ``obj`` as ``str``, ``int``, ``float``, ``bool``, ``list`` or ``dict``.
    """
    # Recurse on dictionaries
    if isinstance(obj, dict):
        new = {}
        for k, v in obj.items():
            key = k if isinstance(k, str) else str(k)
            new[key] = dict_to_yaml(v)
        return new
    # Recurse on lists and tuples
    if isinstance(obj, (list, tuple)):
        return [dict_to_yaml(x) for x in obj]
    # Safe types return as is
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    # Convert Path -> string
    if isinstance(obj, Path):
        return str(obj)
    # Convert numpy array -> nested lists
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    # Convert numpy scalar -> native Python scalar
    if isinstance(obj, np.generic):
        return obj.item()
    # If nothing else is matched use string representation
    return str(obj)


def read_yaml(filename: str | Path) -> Any:
    """
    Read a YAML file.

    Parameters
    ----------
    filename : Union[str, Path]
        YAML file to read.

    Returns
    -------
    Any
        Dictionary of the file.
    """
    with Path(filename).open(encoding="utf-8") as f:
        try:
            return yaml.full_load(f)
        except YAMLError as exception:
            logger.error(exception)
            return {}


def convert_path(path: str | Path) -> Path:
    """
    Ensure path is Path object.

    Parameters
    ----------
    path : str | Path
        Path to be converted.

    Returns
    -------
    Path
        Pathlib object of path.
    """
    return Path().cwd() if path == "./" else Path(path).expanduser()


def get_date_time(strftime: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Get the current date-time as a string for the systems current timezone.

    Parameters
    ----------
    strftime : str
        String for formatting date-time, default is ``%Y-%m-%d %H:%M:%S``.

    Returns
    -------
    str
        Date-time as a string for systems current timezone.
    """
    return datetime.now(tz=datetime.now().astimezone().tzinfo).strftime(strftime)


def dict_to_df(results: dict[str, Any]) -> pd.DataFrame:
    """
    Convert a dictionary of LayOpt results to Pandas DataFrame.

    Typically a set of results is a dictionary with no nesting and the resulting data frame has a single row.

    Parameters
    ----------
    results : dict[str, Any]
        Dictionary to convert to Pandas DataFrame.

    Returns
    -------
    pd.DataFrame
        Data as a Pandas dictionary.
    """
    return pd.DataFrame.from_dict(results, orient="index").T
