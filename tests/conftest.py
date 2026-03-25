# conftest.py
import pytest
import numpy as np

@pytest.fixture
def nodal_coords():
    return np.array([[x,y] for y in range(2) for x in range(5)])

@pytest.fixture
def load_large():
    return 3.75

@pytest.fixture
def load_small():
    return 0.204

@pytest.fixture
def load_direction_default():
    return (0,-1)