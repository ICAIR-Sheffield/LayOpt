"""Fixtures for layopt tests."""

import numpy as np
import numpy.typing as npt
import pytest


@pytest.fixture
def nodal_coords() -> npt.NDArray[np.int32]:
    return np.array([[x, y] for y in range(2) for x in range(5)])
