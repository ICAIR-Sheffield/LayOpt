"""
LayOpt: Adaptive topology optimization of fail-safe trusses.
"""

from __future__ import annotations

from importlib.metadata import version

from packaging.version import Version

__all__ = ["__version__"]


__version__ = version("layopt")
__release__ = ".".join(__version__.split(".")[:-2])
LAYOPT_VERSION = Version(__version__)
if LAYOPT_VERSION.is_prerelease and LAYOPT_VERSION.is_devrelease:
    LAYOPT_BASE_VERSION = str(LAYOPT_VERSION.base_version)
    LAYOPT_COMMIT = str(LAYOPT_VERSION).split("+g")[1]
else:
    LAYOPT_BASE_VERSION = str(LAYOPT_VERSION)
    LAYOPT_COMMIT = ""
# pylint: disable=invalid-name
CONFIG_DOCUMENTATION_REFERENCE = """# For more information on configuration and how to use it:
# https://icair-sheffield.github.io/LayOpt/\n"""
CONFIG_DOCUMENTATION_REFERENCE += f"# Layopt version : {LAYOPT_BASE_VERSION}\n"
CONFIG_DOCUMENTATION_REFERENCE += f"# Commit: {LAYOPT_COMMIT}\n"
