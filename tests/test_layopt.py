"""Tests for the layopt module."""

import os
from typing import Any

import numpy as np
import numpy.typing as npt
import pytest
from syrupy.matchers import path_type

from layopt import layopt

GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"
PRECISION = 6

# pylint: disable=too-many-arguments
# pylint: disable=too-many-locals
# pylint: disable=too-many-positional-arguments
# pylint: disable=too-many-lines
# pylint: disable=protected-access

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
        nodes=structure["nodes"],
        active_members=structure["active_members"],
        dof=structure["dof"],
    )
    assert result.coords == snapshot
    assert result.ndim == snapshot
    assert result.shape == snapshot


@pytest.mark.parametrize(
    ("nodes", "active_members", "dof", "expected"),
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
            id="nodes too short",
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
            id="nodes is None",
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
            id="active_members too short",
            marks=pytest.mark.skip(
                reason="no IndexError as serves as basis for subsetting other arrays"
            ),
        ),
        pytest.param(
            np.asarray([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]),
            None,
            np.asarray([0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 1.0, 1.0]),
            TypeError,
            id="active_members is None",
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
    nodes: npt.NDArray[np.float64],
    active_members: npt.NDArray[np.float64],
    dof: npt.NDArray[np.float64],
    expected,
) -> None:
    """Test for calc_eq_matrix_b()."""
    with pytest.raises(expected):
        layopt.calc_eq_matrix_b(nodes=nodes, active_members=active_members, dof=dof)


@pytest.mark.parametrize(
    ("trussopt_param_fixture", "solver_name"),
    [
        pytest.param(
            "trussopt_param_one_by_one",
            "MOSEK",
            id="1x1_mosek",
        ),
        pytest.param(
            "trussopt_param_two_by_two",
            "MOSEK",
            id="2x2_mosek",
        ),
        pytest.param(
            "trussopt_param_three_by_six_short_cantilever",
            "MOSEK",
            id="short_cantilever_mosek",
        ),
        pytest.param(
            "trussopt_param_eight_by_eight_square_cantilever",
            "MOSEK",
            id="square_cantilever_mosek",
        ),
        pytest.param(
            "trussopt_param_three_by_one_parallel_forces",
            "MOSEK",
            id="parallel_forces_mosek",
        ),
        pytest.param(
            "trussopt_param_eighteen_by_four_spanning",
            "MOSEK",
            id="spanning_example_mosek",
        ),
        pytest.param(
            "trussopt_param_one_by_one",
            "clarabel",
            id="1x1_clarabel",
        ),
        pytest.param(
            "trussopt_param_two_by_two",
            "clarabel",
            id="2x2_clarabel",
        ),
        pytest.param(
            "trussopt_param_three_by_six_short_cantilever",
            "clarabel",
            id="short_cantilever_clarabel",
        ),
        pytest.param(
            "trussopt_param_eight_by_eight_square_cantilever",
            "clarabel",
            id="square_cantilever_clarabel",
        ),
        pytest.param(
            "trussopt_param_three_by_one_parallel_forces",
            "clarabel",
            id="parallel_forces_clarabel",
        ),
        pytest.param(
            "trussopt_param_eighteen_by_four_spanning",
            "clarabel",
            id="spanning_example_clarabel",
        ),
        pytest.param(
            "trussopt_param_eighteen_by_four_spanning_elastic",
            "clarabel",
            id="spanning_example_elastic_clarabel",
        ),
    ],
)
def test_trussopt(
    trussopt_param_fixture: str,
    solver_name: str,
    request,
    snapshot,
) -> None:
    """Regression test for layopt.trussopt()."""
    params = request.getfixturevalue(trussopt_param_fixture)
    params.cvxpy["solver"] = solver_name
    if params.cvxpy["solver"] == "MOSEK" and GITHUB_ACTIONS:
        pytest.skip(
            "MOSEK requires license so test will always fail in continuous integration"
        )

    results = layopt.trussopt(parameters=params)
    # ns-rse 2026-04-15 - results is currently a tuple, the third item of which is now a dictionary of dataframe
    df = results[2]
    results = (results[0], results[1])
    assert results == snapshot(
        matcher=path_type(
            types=(float, np.ndarray),
            replacer=lambda data, _: round_values(data, PRECISION),
        ),
    )
    assert (
        df.T.reset_index(drop=True)
        .drop(["timestamp", "cpu_time_setup", "cpu_time_solve"], axis=1)
        .to_string()
        == snapshot
    )


@pytest.mark.parametrize(
    ("active_indices", "filter_areas", "filtering_threshold", "expected"),
    [
        pytest.param(
            np.asarray([0, 1]),
            np.asarray([10.0, 10.0]),
            0.1,
            {0: 10, 1: 10},
            id="Both areas exceed threshold",
        ),
        pytest.param(
            np.asarray([0, 1]),
            np.asarray([10.0, 0.9]),
            0.1,
            {0: 10},
            id="Only first area exceeds threshold",
        ),
        pytest.param(
            np.asarray([0, 1, 10, 1000]),
            np.asarray([10.0, 0.9, 500.1, 500.2]),
            0.1,
            {10: 500.1, 1000: 500.2},
            id="Last two of four exceed threshold",
        ),
    ],
)
def test_member_area_filtering(
    active_indices: npt.NDArray[np.int8],
    filter_areas: npt.NDArray[np.float64],
    filtering_threshold: float,
    expected: dict[int, np.float64],
) -> None:
    """Test for ``layopt.member_area_filtering()``."""
    assert (
        layopt.member_area_filtering(active_indices, filter_areas, filtering_threshold)
        == expected
    )


# pylint: disable=duplicate-code
@pytest.mark.skipif(
    GITHUB_ACTIONS,
    reason="mosek library requires license so test will always fail in continuous integration",
)
@pytest.mark.parametrize(
    (
        "all_patterns",
        "load_case_active",
        "areas",
        "stress_tensile",
        "stress_compressive",
        "dof",
        "solver",
        "expected_converge",
    ),
    [
        pytest.param(
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
            ],  # all_patterns
            np.asarray([True, True, True, True]),  # load_case_active
            np.ones(10),  # areas
            1,  # stress_tensile
            1,  # stress_compressive
            np.array(
                [0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
            ),  # dof
            "mosek",  # solver
            True,  # expected converge
            id="All active load cases convergence",
        ),
        pytest.param(
            [
                np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
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
            ],  # all_patterns
            np.asarray([True, False]),  # load_case_active
            np.ones(10),  # areas
            1,  # stress_tensile
            1,  # stress_compressive
            np.array(
                [0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
            ),  # dof
            "mosek",  # solver
            False,  # expected converge
            id="One inactive load case no convergence",
        ),
    ],
)
def test_stop_primal_violation(
    nodes: npt.NDArray[np.float64],
    active_members: npt.NDArray[np.float64],
    all_patterns: npt.NDArray[np.float64],
    load_case_active: npt.NDArray[np.float64],
    areas: npt.NDArray[np.float64],
    stress_tensile: int,
    stress_compressive: int,
    dof: npt.NDArray[np.float64],
    solver: str,
    expected_converge: bool,
) -> None:
    """Test for convergence based on whether all load cases active."""
    actual_converge = layopt.stop_primal_violation_pattern(
        nodes,
        active_members,
        areas,
        all_patterns,
        load_case_active,
        dof,
        stress_tensile,
        stress_compressive,
        solver,
        layopt.Structure(layopt.Parameters()),
    )
    assert actual_converge == expected_converge
    assert np.all(load_case_active) is np.bool_(
        True
    )  # checks that violating inactive load cases added


@pytest.mark.parametrize(
    (
        "structure_fixture",
        "stress_tensile",
        "stress_compressive",
        "deflections",
        "expected_num_added",
        "weights",
    ),
    [
        pytest.param(
            "input_one_by_one",
            1,  # stress_tensile
            1,  # stress_compressive
            [np.zeros(8)],  # zero deflections
            0,  # expected_num_added
            [],  # weights (none = plastic problem)
            id="none_added",
        ),
        pytest.param(
            "input_two_by_two",
            1,  # stress_tensile
            1,  # stress_compressive
            [np.ones(18) * 100],  # large deflections
            2,  # expected_num_added
            [],  # weights (none = plastic problem)
            id="large_deflections_added",
        ),
        pytest.param(
            "input_one_by_one",
            1,  # stress_tensile
            1,  # stress_compressive
            [np.zeros(8)],  # zero deflections
            0,  # expected_num_added
            [1],  # weights (none = plastic problem)
            id="elastic_none_added",
        ),
        pytest.param(
            "input_one_by_one",
            1,  # stress_tensile
            1,  # stress_compressive
            [np.ones(8) * 100],  # zero deflections
            0,  # expected_num_added
            [1],  # weights (none = plastic problem)
            id="elastic_large_deflections",
        ),
    ],
)
def test_stop_violation(
    structure_fixture: str,
    request,
    stress_tensile: float,
    stress_compressive: float,
    deflections: list[npt.NDArray[np.float64]],
    expected_num_added: int,
    weights: list[np.float64],
):
    """Test that the function sets members active correctly and returns non-negative integer."""
    structure = request.getfixturevalue(structure_fixture)
    actual_num_added = layopt.stop_violation(
        nodal_coords=structure["nodes"],
        potential_members=structure["active_members"],
        dof=structure["dof"],
        stress_tensile=stress_tensile,
        stress_compressive=stress_compressive,
        deflections=deflections,
        joint_cost=0.0,
        structure=structure,
        weights=weights,  # Currently not testing elastic cases
    )
    assert isinstance(actual_num_added, int)
    assert actual_num_added >= 0
    assert actual_num_added == expected_num_added
