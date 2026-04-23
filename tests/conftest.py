"""Fixtures for layopt tests."""

from typing import Any

import numpy as np
import numpy.typing as npt
import pytest


@pytest.fixture
def nodal_coords() -> npt.NDArray[np.int32]:
    """Coordinates for simple test."""
    return np.array([[x, y] for y in range(2) for x in range(5)])


@pytest.fixture
def c_n():
    """Active members."""
    return np.array(
        [
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
        ]
    )


@pytest.fixture
def input_one_by_one() -> dict[str, npt.NDArray[np.float32]]:
    """``nodal_coords``, ``c_n`` and ``dof`` for a 1x1 structure."""
    return {
        "nodal_coords": np.asarray([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]),
        "c_n": np.asarray(
            [
                [0.0, 1.0, 1.0, True],
                [0.0, 2.0, 1.0, True],
                [0.0, 3.0, 1.41421356, True],
                [1.0, 2.0, 1.41421356, True],
                [1.0, 3.0, 1.0, True],
                [2.0, 3.0, 1.0, True],
            ]
        ),
        "dof": np.asarray([0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 1.0, 1.0]),
    }


@pytest.fixture
def input_two_by_two() -> dict[str, npt.NDArray[np.float32]]:
    """``nodal_coords``, ``c_n`` and ``dof`` for a 2x2 structure."""
    return {
        "nodal_coords": np.asarray(
            [
                [0.0, 0.0],
                [1.0, 0.0],
                [2.0, 0.0],
                [0.0, 1.0],
                [1.0, 1.0],
                [2.0, 1.0],
                [0.0, 2.0],
                [1.0, 2.0],
                [2.0, 2.0],
            ]
        ),
        "c_n": np.asarray(
            [
                [0.0, 1.0, 1.0, False],
                [0.0, 3.0, 1.0, True],
                [0.0, 4.0, 1.41421356, True],
                [0.0, 5.0, 2.23606798, False],
                [1.0, 2.0, 1.0, True],
                [1.0, 3.0, 1.41421356, True],
                [1.0, 4.0, 1.0, True],
                [1.0, 5.0, 1.41421356, True],
                [2.0, 4.0, 1.41421356, True],
                [2.0, 5.0, 1.0, True],
                [3.0, 4.0, 1.0, True],
                [3.0, 6.0, 1.0, True],
                [3.0, 7.0, 1.41421356, True],
                [4.0, 5.0, 1.0, False],
                [4.0, 6.0, 1.41421356, True],
                [4.0, 7.0, 1.0, False],
                [4.0, 8.0, 1.41421356, False],
                [5.0, 6.0, 2.23606798, False],
                [5.0, 7.0, 1.41421356, True],
                [5.0, 8.0, 1.0, True],
                [6.0, 7.0, 1.0, True],
                [7.0, 8.0, 1.0, True],
            ]
        ),
        "dof": np.asarray(
            [
                0.0,
                0.0,
                1.0,
                1.0,
                1.0,
                1.0,
                0.0,
                0.0,
                1.0,
                1.0,
                1.0,
                1.0,
                0.0,
                0.0,
                1.0,
                1.0,
                1.0,
                1.0,
            ]
        ),
    }


@pytest.fixture
def input_three_by_six() -> dict[str, npt.NDArray[np.float32]]:
    """``nodal_coords``, ``c_n`` and ``dof`` for a 3x6 structure."""
    return {
        "nodal_coords": np.asarray(
            [
                [0.0, 0.0],
                [1.0, 0.0],
                [2.0, 0.0],
                [3.0, 0.0],
                [0.0, 1.0],
                [1.0, 1.0],
                [2.0, 1.0],
                [3.0, 1.0],
                [0.0, 2.0],
                [1.0, 2.0],
                [2.0, 2.0],
                [3.0, 2.0],
                [0.0, 3.0],
                [1.0, 3.0],
                [2.0, 3.0],
                [3.0, 3.0],
                [0.0, 4.0],
                [1.0, 4.0],
                [2.0, 4.0],
                [3.0, 4.0],
                [0.0, 5.0],
                [1.0, 5.0],
                [2.0, 5.0],
                [3.0, 5.0],
                [0.0, 6.0],
                [1.0, 6.0],
                [2.0, 6.0],
                [3.0, 6.0],
            ]
        ),
        "c_n": np.asarray(
            [
                [0.0, 1.0, 1.0, True],
                [0.0, 4.0, 1.0, True],
                [0.0, 5.0, 1.41421356, True],
                [1.0, 2.0, 1.0, True],
                [1.0, 4.0, 1.41421356, True],
                [1.0, 5.0, 1.0, True],
                [1.0, 6.0, 1.41421356, True],
                [2.0, 3.0, 1.0, True],
                [2.0, 5.0, 1.41421356, True],
                [2.0, 6.0, 1.0, True],
                [2.0, 7.0, 1.41421356, True],
                [3.0, 6.0, 1.41421356, True],
                [3.0, 7.0, 1.0, True],
                [4.0, 5.0, 1.0, True],
                [4.0, 8.0, 1.0, True],
                [4.0, 9.0, 1.41421356, True],
                [5.0, 6.0, 1.0, True],
                [5.0, 8.0, 1.41421356, True],
                [5.0, 9.0, 1.0, True],
                [5.0, 10.0, 1.41421356, True],
                [6.0, 7.0, 1.0, True],
                [6.0, 9.0, 1.41421356, True],
                [6.0, 10.0, 1.0, True],
                [6.0, 11.0, 1.41421356, True],
                [7.0, 10.0, 1.41421356, True],
                [7.0, 11.0, 1.0, True],
                [8.0, 9.0, 1.0, True],
                [8.0, 12.0, 1.0, True],
                [8.0, 13.0, 1.41421356, True],
                [9.0, 10.0, 1.0, True],
                [9.0, 12.0, 1.41421356, True],
                [9.0, 13.0, 1.0, True],
                [9.0, 14.0, 1.41421356, True],
                [10.0, 11.0, 1.0, True],
                [10.0, 13.0, 1.41421356, True],
                [10.0, 14.0, 1.0, True],
                [10.0, 15.0, 1.41421356, True],
                [11.0, 14.0, 1.41421356, True],
                [11.0, 15.0, 1.0, True],
                [12.0, 13.0, 1.0, True],
                [12.0, 16.0, 1.0, True],
                [12.0, 17.0, 1.41421356, True],
                [13.0, 14.0, 1.0, True],
                [13.0, 16.0, 1.41421356, True],
                [13.0, 17.0, 1.0, True],
                [13.0, 18.0, 1.41421356, True],
                [14.0, 15.0, 1.0, True],
                [14.0, 17.0, 1.41421356, True],
                [14.0, 18.0, 1.0, True],
                [14.0, 19.0, 1.41421356, True],
                [15.0, 18.0, 1.41421356, True],
                [15.0, 19.0, 1.0, True],
                [16.0, 17.0, 1.0, True],
                [16.0, 20.0, 1.0, True],
                [16.0, 21.0, 1.41421356, True],
                [17.0, 18.0, 1.0, True],
                [17.0, 20.0, 1.41421356, True],
                [17.0, 21.0, 1.0, True],
                [17.0, 22.0, 1.41421356, True],
                [18.0, 19.0, 1.0, True],
                [18.0, 21.0, 1.41421356, True],
                [18.0, 22.0, 1.0, True],
                [18.0, 23.0, 1.41421356, True],
                [19.0, 22.0, 1.41421356, True],
                [19.0, 23.0, 1.0, True],
                [20.0, 21.0, 1.0, True],
                [20.0, 24.0, 1.0, True],
                [20.0, 25.0, 1.41421356, True],
                [21.0, 22.0, 1.0, True],
                [21.0, 24.0, 1.41421356, True],
                [21.0, 25.0, 1.0, True],
                [21.0, 26.0, 1.41421356, True],
                [22.0, 23.0, 1.0, True],
                [22.0, 25.0, 1.41421356, True],
                [22.0, 26.0, 1.0, True],
                [22.0, 27.0, 1.41421356, True],
                [23.0, 26.0, 1.41421356, True],
                [23.0, 27.0, 1.0, True],
                [24.0, 25.0, 1.0, True],
                [25.0, 26.0, 1.0, True],
                [26.0, 27.0, 1.0, True],
            ]
        ),
        "dof": np.asarray(
            [
                0.0,
                0.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                0.0,
                0.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                0.0,
                0.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                0.0,
                0.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                0.0,
                0.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                0.0,
                0.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                0.0,
                0.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
            ]
        ),
    }


@pytest.fixture
def trussopt_param_three_by_six_short_cantilever() -> dict[str, Any]:
    """Input parameters for 3x6 structure for ``layopt.trussopt()``."""
    return {
        "width": 3,
        "height": 6,
        "st": 1,
        "sc": 1,
        "jc": 0,
        "loaded_points": np.asarray([[3, 3]]),
        "load_direction": (0, -1),
        "load_large": 50,
        "load_small": 5,
        "max_length": 18,
        "support_points": np.asarray([[]]),
        "filter_level": None,
        "primal_method": "load_factor",
        "problem_name": "short cantilever",
        "save_to_csv": True,
        "csv_filename": "short_cantilever.csv",
        "notes": "short cantliever test",
    }


@pytest.fixture
def trussopt_param_eight_by_eight_square_cantilever() -> dict[str, Any]:
    """Input parameters for 8x8 structure for ``layopt.trussopt()``."""
    return {
        "width": 8,
        "height": 8,
        "st": 1,
        "sc": 1,
        "jc": 0,
        "loaded_points": np.asarray([[8, 0], [8, 4]]),
        "load_direction": (0, -1),
        "load_large": 50,
        "load_small": 5,
        "max_length": 15,
        "support_points": np.asarray([[]]),
        "filter_level": None,
        "primal_method": "load_factor",
        "problem_name": "square cantilever",
        "save_to_csv": True,
        "csv_filename": "square_cantilever.csv",
        "notes": "square cantliever test",
    }


@pytest.fixture
def trussopt_param_three_by_one_parallel_forces() -> dict[str, Any]:
    """Input parameters for 3x1 (parallel) structure for ``layopt.trussopt()``."""
    return {
        "width": 3,
        "height": 1,
        "st": 1,
        "sc": 1,
        "jc": 0,
        "loaded_points": np.asarray([[3, 0], [3, 1]]),
        "load_direction": (0, -1),
        "load_large": 50,
        "load_small": 5,
        "max_length": 2.5,
        "support_points": np.asarray([[]]),
        "filter_level": None,
        "primal_method": "load_factor",
        "problem_name": "parallel forces",
        "save_to_csv": True,
        "csv_filename": "parallel_forces.csv",
        "notes": "parallel forces test",
    }


@pytest.fixture
def trussopt_param_eighteen_by_four_spanning() -> dict[str, Any]:
    """Input parameters for 18x4 (spanning) structure for ``layopt.trussopt()``."""
    return {
        "width": 18,
        "height": 4,
        "st": 1,
        "sc": 1,
        "jc": 0,
        "loaded_points": np.asarray(
            [
                [0.0, 4],
                [2.0, 4],
                [4.0, 4],
                [6.0, 4],
                [8.0, 4],
                [10.0, 4],
                [12.0, 4],
                [14.0, 4],
                [16.0, 4],
                [18.0, 4],
            ]
        ),
        "load_direction": (0, -1),
        "load_large": 3.75,
        "load_small": 0.204,
        "max_length": 36,
        "support_points": np.asarray([[0, 0], [18, 0]]),
        "filter_level": None,
        "primal_method": "load_factor",
        "problem_name": "spanning example",
        "save_to_csv": True,
        "csv_filename": "spanning_example.csv",
        "notes": "spanning example test",
    }


@pytest.fixture
def sample_csv_results() -> dict[str, Any]:
    """Sample results for testing csv output."""
    return {
        "timestamp": "2026-03-04 15:30:00",
        "problem_name": "test_problem",
        "width": 8,
        "height": 8,
        "n_load_points": 2,
        "n_patterns_total": 4,
        "n_patterns_active": 3,
        "load_large": 50,
        "load_small": 5,
        "iterations": 12,
        "final_volume": 123.456,
        "n_members_final": 87,
        "n_nodes": 81,
        "n_ground_structure": 1234,
        "cpu_time_setup": 0.234,
        "cpu_time_solve": 12.456,
        "primal_method": True,
        "notes": "Test run",
    }
