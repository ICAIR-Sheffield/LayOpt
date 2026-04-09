"""Module functions for working with configuration files."""

from __future__ import annotations

from argparse import Namespace
from datetime import datetime
from pathlib import Path
from pkgutil import get_data
from time import tzname
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
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
    # Otherwise we are writing after 'layopt optimise' and config is a dictionary, this won't have a 'filename'
    # key/value pair
    elif isinstance(args, dict):
        output_dir = (
            Path("./") if args["output_dir"] is None else Path(args["output_dir"])
        )
        # Add missing 'filename' key/value pair
        filename = f"config_{get_date_time(strftime='%Y-%m-%d-%H%M%S')}.yaml"
    else:
        msg = f"args is neither 'Namespace' or 'dict' : {type(args)}"
        raise TypeError(msg)
    if ".yaml" not in str(filename) and ".yml" not in str(filename):
        config_path = output_dir / f"{filename}.yaml"
    else:
        config_path = output_dir / filename
    logger_msg = "A sample configuration has been written to"
    try:
        config = get_data(package="layopt", resource="default_config.yaml")
    except FileNotFoundError as exc:
        msg = (
            "There was a problem loading 'default_config.yaml' try reinstalling LayOpt."
        )
        raise (FileNotFoundError(msg)) from exc
    with config_path.open("w", encoding="utf-8") as f:
        try:
            f.write(f"# Config generated {get_date_time()}\n")
            f.write(f"{CONFIG_DOCUMENTATION_REFERENCE}")
            f.write(config.decode("utf-8"))
        except:  # noqa: E722, pylint: disable=W0702
            logger.error(f"Failed to write config to : {config_path}")
    logger.info(f"{logger_msg} : {config_path!s}")


def read_yaml(filename: str | Path) -> dict:
    """
    Read a YAML file.

    Parameters
    ----------
    filename : Union[str, Path]
        YAML file to read.

    Returns
    -------
    Dict
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


def get_date_time(strftime: str = "%Y-%m-%d %H:%M:%S", tz: str | None = None) -> str:
    """
    Get the current date-time.

    Parameters
    ----------
    strftime : str
        String for formatting date-time, default is ``%Y-%m-%d %H:%M:%S``.
    tz : str
        Timezone, default is ``None`` in which case ``ZoneInfo`` is used.

    Returns
    -------
    str
        Date-time as a string.
    """
    timezone = ZoneInfo(tzname[0]) if tz is None else ZoneInfo(tz)
    return datetime.now(tz=timezone).strftime(strftime)


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
