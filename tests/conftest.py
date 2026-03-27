# conftest.py
import numpy as np
import pytest


@pytest.fixture
def nodal_coords():
    return np.array([[x, y] for y in range(2) for x in range(5)])


@pytest.fixture
def c_n():
    return np.array([
        [0, 1, 1, True],
        [1, 2, 1, True],
        [2, 3, 1, True],
        [3, 4, 1, True],
        [5, 6, 1, True],
        [6, 7, 1, True],
        [7, 8, 1, True],
        [8, 9, 1, True],
        [0, 5, 1, True],
        [4, 9, 1, True],
    ])


@pytest.fixture
def areas():
    return np.ones(10)


@pytest.fixture
def dof():
    return np.array([0,0,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1,1,1,1])


@pytest.fixture
def load_direction_default():
    return (0, -1)


