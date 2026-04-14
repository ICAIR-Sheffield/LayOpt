"""Tests for the layopt module."""

import os
from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt
import pandas as pd
import pytest
from syrupy.matchers import path_type

from layopt import layopt

GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"
PRECISION = 8

# pylint: disable=too-many-arguments
# pylint: disable=too-many-locals
# pylint: disable=too-many-positional-arguments

np.set_printoptions(precision=PRECISION)


def round_values(to_be_rounded: Any, precision: int) -> Any:
    """
    Round values conditional on type (``float`` or ``np.ndarray``).

    Parameters
    ----------
    to_be_rounded : Any
        Parameter to be rounded.
    precision : int
        Significant digits to round to.

    Returns
    -------
        Rounded value if either ``float`` or ``np.ndarray`` is provided.
    """
    if isinstance(to_be_rounded, float):
        return round(to_be_rounded, precision)
    if isinstance(to_be_rounded, np.ndarray):
        return np.round(to_be_rounded, precision)
    return to_be_rounded


@pytest.mark.parametrize(
    ("structure_fixture"),
    [
        pytest.param(
            "input_one_by_one",
            id="1x1",
        ),
        pytest.param(
            "input_two_by_two",
            id="2x2",
        ),
        pytest.param(
            "input_three_by_six",
            id="3x6",
        ),
    ],
)
def test_calc_eq_matrix_b(
    structure_fixture: str,
    request,
    snapshot,
) -> None:
    """Test for calc_eq_matrix_b()."""
    structure = request.getfixturevalue(structure_fixture)
    result = layopt.calc_eq_matrix_b(
        nodal_coords=structure["nodal_coords"],
        c_n=structure["c_n"],
        dof=structure["dof"],
    )
    assert result.coords == snapshot
    assert result.ndim == snapshot
    assert result.shape == snapshot


@pytest.mark.parametrize(
    ("nodal_coords", "c_n", "dof", "expected"),
    [
        pytest.param(
            np.asarray([[0.0, 0.0], [1.0, 0.0]]),
            np.asarray(
                [
                    [0.0, 1.0, 1.0, 1.0],
                    [0.0, 2.0, 1.0, 1.0],
                    [0.0, 3.0, 1.41421356, 1.0],
                    [1.0, 2.0, 1.41421356, 1.0],
                    [1.0, 3.0, 1.0, 1.0],
                    [2.0, 3.0, 1.0, 1.0],
                ]
            ),
            np.asarray([0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 1.0, 1.0]),
            IndexError,
            id="nodal_coords too short",
        ),
        pytest.param(
            None,
            np.asarray(
                [
                    [0.0, 1.0, 1.0, 1.0],
                    [0.0, 2.0, 1.0, 1.0],
                    [0.0, 3.0, 1.41421356, 1.0],
                    [1.0, 2.0, 1.41421356, 1.0],
                    [1.0, 3.0, 1.0, 1.0],
                    [2.0, 3.0, 1.0, 1.0],
                ]
            ),
            np.asarray([0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 1.0, 1.0]),
            TypeError,
            id="nodal_coords is None",
        ),
        pytest.param(
            np.asarray([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]),
            np.asarray(
                [
                    [0.0, 1.0, 1.0, 1.0],
                    [0.0, 2.0, 1.0, 1.0],
                    [0.0, 3.0, 1.41421356, 1.0],
                ]
            ),
            np.asarray([0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 1.0, 1.0]),
            IndexError,
            id="c_n too short",
            marks=pytest.mark.skip(
                reason="no IndexError as serves as basis for subsetting other arrays"
            ),
        ),
        pytest.param(
            np.asarray([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]),
            None,
            np.asarray([0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 1.0, 1.0]),
            TypeError,
            id="c_n is None",
        ),
        pytest.param(
            np.asarray([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]),
            np.asarray(
                [
                    [0.0, 1.0, 1.0, 1.0],
                    [0.0, 2.0, 1.0, 1.0],
                    [0.0, 3.0, 1.41421356, 1.0],
                    [1.0, 2.0, 1.41421356, 1.0],
                    [1.0, 3.0, 1.0, 1.0],
                    [2.0, 3.0, 1.0, 1.0],
                ]
            ),
            np.asarray([0.0, 0.0, 1.0, 1.0]),
            IndexError,
            id="dof too short",
        ),
        pytest.param(
            np.asarray([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]),
            np.asarray(
                [
                    [0.0, 1.0, 1.0, 1.0],
                    [0.0, 2.0, 1.0, 1.0],
                    [0.0, 3.0, 1.41421356, 1.0],
                    [1.0, 2.0, 1.41421356, 1.0],
                    [1.0, 3.0, 1.0, 1.0],
                    [2.0, 3.0, 1.0, 1.0],
                ]
            ),
            None,
            TypeError,
            id="dof is None",
        ),
    ],
)
def test_calc_eq_matrix_b_errors(
    nodal_coords: npt.NDArray[np.float32],
    c_n: npt.NDArray[np.float32],
    dof: npt.NDArray[np.float32],
    expected,
) -> None:
    """Test for calc_eq_matrix_b()."""
    with pytest.raises(expected):
        layopt.calc_eq_matrix_b(nodal_coords=nodal_coords, c_n=c_n, dof=dof)


@pytest.mark.skipif(
    GITHUB_ACTIONS,
    reason="mosek library requires license so test will always fail in continuous integration",
)
@pytest.mark.parametrize(
    ("trussopt_param_fixture"),
    [
        pytest.param(
            "trussopt_param_three_by_six_short_cantilever",
            id="short cantilever",
        ),
        pytest.param(
            "trussopt_param_eight_by_eight_square_cantilever", id="square cantilever"
        ),
        pytest.param(
            "trussopt_param_three_by_one_parallel_forces", id="parallel forces"
        ),
        pytest.param("trussopt_param_eighteen_by_four_spanning", id="spanning example"),
    ],
)
def test_trussopt(
    trussopt_param_fixture: str,
    tmp_path: Path,
    request,
    snapshot,
) -> None:
    """Regression test for layopt.trussopt()."""
    params = request.getfixturevalue(trussopt_param_fixture)
    results = layopt.trussopt(
        width=params["width"],
        height=params["height"],
        stress_tensile=params["st"],
        stress_compressive=params["sc"],
        joint_cost=params["jc"],
        loaded_points=params["loaded_points"],
        load_direction=params["load_direction"],
        load_large=params["load_large"],
        load_small=params["load_small"],
        max_length=params["max_length"],
        support_points=params["support_points"],
        member_area_filtering=params["member_area_filtering"],
        primal_method=params["primal_method"],
        problem_name=params["problem_name"],
        save_to_csv=params["save_to_csv"],
        csv_filename=tmp_path / params["csv_filename"],
        notes=params["notes"],
    )
    assert Path(tmp_path / params["csv_filename"]).is_file()
    # Round values
    assert results == snapshot(
        matcher=path_type(
            types=(float, np.ndarray),
            replacer=lambda data, _: round_values(data, PRECISION),
        ),
    )
    results = pd.read_csv(tmp_path / params["csv_filename"])
    assert (
        results.drop(
            ["timestamp", "cpu_time_setup", "cpu_time_solve"], axis=1
        ).to_string()
        == snapshot
    )


@pytest.mark.parametrize(
    (
        "loaded_points",
        "load_large",
        "load_small",
        "load_direction_default",
        "expected_pattern_count",
    ),
    [
        pytest.param(
            np.array([[0.0, 1]]), 3.75, 0.204, (0, -1), 2, id="1 load point (2^1)"
        ),
        pytest.param(
            np.array([[0.0, 1], [4.0, 1]]),
            3.75,
            0.204,
            (0, -1),
            4,
            id="2 load points (2^2)",
        ),
        pytest.param(
            np.array([[0.0, 1], [2.0, 1], [4.0, 1]]),
            3.75,
            0.204,
            (0, -1),
            8,
            id="3 load points (2^3)",
        ),
    ],
    ids=["1_point", "2_points", "3_points"],
)
def test_make_pattern_loads_num_load_patterns(
    nodal_coords: npt.NDArray,
    load_large: float,
    load_small: float,
    load_direction_default: tuple[float, float],
    loaded_points: npt.NDArray,
    expected_pattern_count: int,
):
    all_patterns, _, _ = layopt.make_pattern_loads(
        nodal_coords, loaded_points, load_large, load_small, load_direction_default
    )
    assert len(all_patterns) == expected_pattern_count


@pytest.mark.parametrize(
    (
        "loaded_points",
        "load_large",
        "load_small",
        "direction",
        "expected_pattern_count",
        "expected_patterns",
        "expected_pattern_description",
    ),
    [
        pytest.param(
            np.asarray([[0.0, 1], [4.0, 1]]),
            3.75,
            0.204,
            (0.0, -1.0),
            4,
            [
                np.array(
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -3.75, 0, 0, 0, 0, 0, 0, 0, -3.75]
                ),
                np.array(
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        -3.75,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        -0.204,
                    ]
                ),
                np.array(
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        -0.204,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        -3.75,
                    ]
                ),
                np.array(
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        -0.204,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        -0.204,
                    ]
                ),
            ],
            ["pt0=L, pt1=L", "pt0=L, pt1=S", "pt0=S, pt1=L", "pt0=S, pt1=S"],
            id="vertical",
        ),
        pytest.param(
            np.asarray([[0.0, 1], [4.0, 1]]),
            3.75,
            0.204,
            (1.0, 0.0),
            4,
            [
                np.array(
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3.75, 0, 0, 0, 0, 0, 0, 0, 3.75, 0]
                ),
                np.array(
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3.75, 0, 0, 0, 0, 0, 0, 0, 0.204, 0]
                ),
                np.array(
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.204, 0, 0, 0, 0, 0, 0, 0, 3.75, 0]
                ),
                np.array(
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.204, 0, 0, 0, 0, 0, 0, 0, 0.204, 0]
                ),
            ],
            ["pt0=L, pt1=L", "pt0=L, pt1=S", "pt0=S, pt1=L", "pt0=S, pt1=S"],
            id="horizontal",
        ),
        pytest.param(
            np.asarray([[0.1, 0.9], [4.0, 1]]),
            3.75,
            0.204,
            (0.0, -1.0),
            4,
            [
                np.array(
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -3.75, 0, 0, 0, 0, 0, 0, 0, -3.75]
                ),
                np.array(
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        -3.75,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        -0.204,
                    ]
                ),
                np.array(
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        -0.204,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        -3.75,
                    ]
                ),
                np.array(
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        -0.204,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        -0.204,
                    ]
                ),
            ],
            ["pt0=L, pt1=L", "pt0=L, pt1=S", "pt0=S, pt1=L", "pt0=S, pt1=S"],
            id="Off node snapping",
        ),
    ],
)
def test_make_pattern_loads_load_directions_and_node_snapping(
    nodal_coords: npt.NDArray,
    load_large: float,
    load_small: float,
    loaded_points: npt.NDArray[np.float32],
    direction,
    expected_pattern_count: int,
    expected_patterns: npt.NDArray[np.float32],
    expected_pattern_description: list[str],
):
    """Test vertical loads, horizontal loads, and snapping to nearest nodes."""
    all_patterns, base_load, pattern_description = layopt.make_pattern_loads(
        nodal_coords, loaded_points, load_large, load_small, direction
    )
    assert len(all_patterns) == expected_pattern_count
    np.testing.assert_equal(all_patterns, expected_patterns)
    np.testing.assert_equal(base_load, expected_patterns[0])
    assert pattern_description == expected_pattern_description


@pytest.mark.parametrize(
    ("loaded_points", "error", "msg"),
    [
        pytest.param(
            [], TypeError, "'loaded_points' is not a numpy array", id="empty list"
        ),
        pytest.param(
            np.asarray([[]]),
            AssertionError,
            "Need at least one load point",
            id="empty numpy array",
        ),
        pytest.param(
            None, TypeError, "'loaded_points' is not a numpy array", id="None"
        ),
        pytest.param(
            0.0, TypeError, "'loaded_points' is not a numpy array", id="float"
        ),
    ],
)
def test_make_pattern_loads_zero_load_points_error(
    nodal_coords: npt.NDArray,
    loaded_points: Any,
    error,
    msg: str,
):
    """Test that 0 load points raises AssertionError from ``layopt.make_pattern_loads()``."""
    with pytest.raises(error, match=msg):
        layopt.make_pattern_loads(
            nodal_coords=nodal_coords,
            loaded_points=loaded_points,
            load_large=3.75,
            load_small=0.204,
            load_direction=(0.0, -1.0),
        )


@pytest.mark.parametrize(
    (
        "all_patterns",
        "active_load_cases",
        "areas",
        "stress_tensile",
        "stress_compressive",
        "dof",
        "expected_converge",
    ),
    [
        pytest.param(
            [
                np.array(
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -3.75, 0, 0, 0, 0, 0, 0, 0, -3.75]
                ),  # all_patterns
                np.array(
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        -3.75,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        -0.204,
                    ]
                ),
                np.array(
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        -0.204,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        -3.75,
                    ]
                ),
                np.array(
                    [
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        -0.204,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        -0.204,
                    ]
                ),
            ],
            np.asarray([1, 1, 1, 1]),  # active_load_cases
            np.ones(10),  # areas
            1,  # stress_tensile
            1,  # stress_compressive
            np.array(
                [0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
            ),  # dof
            True,  # expected converge
            id="All active load cases",
        ),
    ],
)
def test_stop_primal_violation_active_convergence(
    nodal_coords: npt.NDArray,
    c_n: npt.NDArray,
    all_patterns: npt.NDArray,
    active_load_cases: npt.NDArray,
    areas: npt.NDArray,
    stress_tensile: int,
    stress_compressive: int,
    dof: npt.NDArray,
    expected_converge: list[int],
) -> None:
    """Test that all load cases active converges"""
    actual_converge = layopt.stop_primal_violation_pattern(
        nodal_coords,
        c_n,
        areas,
        all_patterns,
        active_load_cases,
        dof,
        stress_tensile,
        stress_compressive,
    )
    assert actual_converge == expected_converge


@pytest.mark.parametrize(
    (
        "structure_fixture",
        "stress_tensile",
        "stress_compressive",
        "deflections",
        "expected_num_added",
    ),
    [
        pytest.param(
            "input_one_by_one",
            1,  # stress_tensile
            1,  # stress_compressive
            [np.zeros(8)],  # zero deflections
            0,  # expected_num_added
            id="none_added",
        ),
        pytest.param(
            "input_two_by_two",
            1,  # stress_tensile
            1,  # stress_compressive
            [np.ones(18) * 100],  # large deflections
            2,  # expected_num_added
            id="large_deflections_added",
        ),
    ],
)
def test_stop_violation(
    structure_fixture: str,
    request,
    stress_tensile: float,
    stress_compressive: float,
    deflections: list,
    expected_num_added: int,
):
    """Test that the function sets members active correctly and returns non-negative integer."""
    structure = request.getfixturevalue(structure_fixture)
    actual_num_added = layopt.stop_violation(
        nodal_coords=structure["nodal_coords"],
        potential_members=structure["c_n"],
        dof=structure["dof"],
        stress_tensile=stress_tensile,
        stress_compressive=stress_compressive,
        deflections=deflections,
        joint_cost=0.0,
    )
    assert isinstance(actual_num_added, int)
    assert actual_num_added >= 0
    assert actual_num_added == expected_num_added
