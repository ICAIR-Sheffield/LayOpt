# conftest.py
import numpy as np
import pytest


@pytest.fixture
def nodal_coords():
    return np.array([[x, y] for y in range(2) for x in range(5)])

@pytest.fixture
def load_direction_default():
    return (0, -1)
