from __future__ import annotations

import importlib.metadata

import layopt as m


def test_version():
    assert importlib.metadata.version("layopt") == m.__version__
