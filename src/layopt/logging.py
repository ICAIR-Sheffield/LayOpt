"""Configur logging with loguru."""

from __future__ import annotations

import sys

from loguru import logger


def setup(level: str = "INFO") -> None:
    """
    Loguru setup with the required logging level and format.

    Parameters
    ----------
    level : str
        Log level, default is ``INFO``, other options ``WARNING``, ``DEBUG`` etc.
    """
    logger.remove()
    logger.add(sys.stderr)
    # Set the format to have blue time, green file, module, function and line, and white message
    logger.add(
        sys.stderr,
        colorize=True,
        level=level.upper(),
        format="<blue>{time:HH:mm:ss}</blue> | <level>{level}</level> |"
        "<magenta>{file}</magenta>:<magenta>{module}</magenta>:<magenta>"
        "{function}</magenta>:<magenta>{line}</magenta> | <level>{message}</level>",
    )
