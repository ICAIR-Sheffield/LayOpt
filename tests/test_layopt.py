"""Tests for the layopt module."""

import os
from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt
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


@pytest.mark.skipif(
    GITHUB_ACTIONS,
    reason="mosek library requires license so test will always fail in continuous integration",
)
@pytest.mark.parametrize(
    (
        "width",
        "height",
        "st",
        "sc",
        "jc",
        "loaded_points",
        "load_direction",
        "load_large",
        "load_small",
        "max_length",
        "support_points",
        "filtering",
        "primal_method",
        "problem_name",
        "save_to_csv",
        "csv_filename",
        "notes",
    ),
    [
        pytest.param(
            3,  # width
            6,  # height
            1,  # st
            1,  # sc
            0,  # jc
            [[3, 3]],  # loaded_points
            (0, -1),  # load_direction
            50,  # load_large
            5,  # load_small
            18,  # max_length
            [],  # support_points
            False,  # filter
            "load_factor",  # primal_method
            "short cantilever",  # problem_name
            True,  # save_to_csv
            "short_cantilever.csv",  # csv_filename
            "short cantliever test",  # notes
            id="short cantilever",
        ),
        pytest.param(
            8,  # width
            8,  # height
            1,  # st
            1,  # sc
            0,  # jc
            [[8, 0], [8, 4]],  # loaded_points
            (0, -1),  # load_direction
            50,  # load_large
            5,  # load_small
            15,  # max_length
            [],  # support_points
            False,  # filter
            "load_factor",  # primal_method
            "square cantilever",  # problem_name
            True,  # save_to_csv
            "square_cantilever.csv",  # csv_filename
            "square cantliever test",  # notes
            id="square cantilever",
        ),
        pytest.param(
            3,  # width
            1,  # height
            1,  # st
            1,  # sc
            0,  # jc
            [[3, 0], [3, 1]],  # loaded_points
            (0, -1),  # load_direction
            50,  # load_large
            5,  # load_small
            2.5,  # max_length
            [],  # support_points
            False,  # filter
            "load_factor",  # primal_method
            "parallel forces",  # problem_name
            True,  # save_to_csv
            "parallel_forces.csv",  # csv_filename
            "parallel forces test",  # notes
            id="parallel forces",
        ),
        pytest.param(
            18,  # width
            4,  # height
            1,  # st
            1,  # sc
            0,  # jc
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
            ],  # loaded_points
            (0, -1),  # load_direction
            3.75,  # load_large
            0.204,  # load_small
            36,  # max_length
            [[0, 0], [18, 0]],  # support_points
            False,  # filter
            "load_factor",  # primal_method
            "spanning example",  # problem_name
            True,  # save_to_csv
            "spanning_example.csv",  # csv_filename
            "spanning example test",  # notes
            id="spanning example",
        ),
    ],
)
def test_testname(
    width: int,
    height: int,
    st: int,
    sc: int,
    jc: int,
    loaded_points: list[list[int]],
    load_direction: tuple[float, float],
    load_large: int,
    load_small: int,
    max_length: int,
    support_points: list[list[int]],
    filtering: bool,
    primal_method: str,
    problem_name: str,
    save_to_csv: bool,
    csv_filename: str,
    notes: str,
    snapshot,
) -> None:
    """Regression test for layopt.trussopt()."""
    results = layopt.trussopt(
        width=width,
        height=height,
        stress_tensile=st,
        stress_compressive=sc,
        joint_cost=jc,
        loaded_points=loaded_points,
        load_direction=load_direction,
        load_large=load_large,
        load_small=load_small,
        max_length=max_length,
        support_points=support_points,
        member_area_filtering=filtering,
        primal_method=primal_method,
        problem_name=problem_name,
        save_to_csv=save_to_csv,
        csv_filename=csv_filename,
        notes=notes,
    )
    assert Path(csv_filename).is_file()
    # Round values
    assert results == snapshot(
        matcher=path_type(
            types=(float, np.ndarray),
            replacer=lambda data, _: round_values(data, PRECISION),
        ),
    )
    # ns-rse 2026-03-17 - load results and test against snapshot


@pytest.mark.parametrize(
    "loaded_points, load_large, load_small, expected_pattern_count",
    [
        pytest.param(
            [[0.0, 1]],
            3.75,  # load_large
            0.204,  # load_small
            2,  # 1 load point -> 2^1 = 2
            id="1_point",
        ),
        pytest.param(
            [[0.0, 1], [4.0, 1]],
            3.75,  # load_large
            0.204,  # load_small
            4,  # 2 load points -> 2^2 = 4
            id="2_points",
        ),
        pytest.param(
            [[0.0, 1], [2.0, 1], [4.0, 1]],
            3.75,  # load_large
            0.204,  # load_small
            8,  # 3 load points -> 2^3 = 8
            id="3_points",
        ),
    ],
)
def test_make_pattern_loads_num_load_patterns(
    nodal_coords: npt.NDArray,
    load_large: float,
    load_small: float,
    load_direction_default: tuple[float, float],
    loaded_points: list,
    expected_pattern_count: int,
):
    """Test that number of load patterns is as expected."""
    all_patterns, _, _ = layopt.make_pattern_loads(
        nodal_coords, loaded_points, load_large, load_small, load_direction_default
    )
    assert len(all_patterns) == expected_pattern_count


@pytest.mark.parametrize(
    "loaded_points, direction, load_large, load_small, expected_patterns",
    [
        pytest.param(
            # Vertical Load (negative y)
            [[0.0, 1], [4.0, 1]],
            (0, -1),
            3.75,  # load_large
            0.204,  # load_small
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
            id="Vertical load (negative y)",
        ),
        pytest.param(
            # Horizontal Load (positive x)
            [[0.0, 1], [4.0, 1]],
            (1, 0),
            3.75,  # load_large
            0.204,  # load_small
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
            id="Horizontal load (positive x)",
        ),
        pytest.param(
            # Load point not strictly on a node (snaps to nearest)
            [[0.1, 0.9], [4.0, 1]],
            (0, -1),
            3.75,  # load_large
            0.204,  # load_small
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
            id="Node snapping for load point",
        ),
    ],
)
def test_make_pattern_loads_load_directions_and_node_snapping(
    nodal_coords: npt.NDArray,
    load_large: float,
    load_small: float,
    loaded_points,
    direction,
    expected_patterns,
):
    """Test vertical loads, horizontal loads, and snapping to nearest nodes."""
    all_patterns, base_load, _ = layopt.make_pattern_loads(
        nodal_coords, loaded_points, load_large, load_small, direction
    )

    # Check all pattern variations are correct
    np.testing.assert_equal(all_patterns, expected_patterns)

    # Check that base_load is correctly extracted as the first pattern
    np.testing.assert_equal(base_load, expected_patterns[0])


@pytest.mark.parametrize(
    "loaded_points, load_large, load_small, expected_pattern_descriptions",
    [
        pytest.param(
            [[0.0, 1], [4.0, 1]],
            3.75,
            0.204,
            ["pt0=L, pt1=L", "pt0=L, pt1=S", "pt0=S, pt1=L", "pt0=S, pt1=S"],
            id="4_pattern_descriptions",
        )
    ],
)
def test_make_pattern_loads_pattern_descriptions(
    nodal_coords: npt.NDArray,
    load_large: float,
    load_small: float,
    load_direction_default: tuple[float, float],
    loaded_points,
    expected_pattern_descriptions,
):
    """Test that the 2^n pattern descriptions are accurate."""
    _, _, pattern_descriptions = layopt.make_pattern_loads(
        nodal_coords, loaded_points, load_large, load_small, load_direction_default
    )
    assert pattern_descriptions == expected_pattern_descriptions


@pytest.mark.xfail(reason="AssertionError not being raised")
def test_make_pattern_loads_zero_load_points_error(
    nodal_coords: npt.NDArray,
    load_direction_default: tuple[float, float],
):
    """Test that 0 load points raises ``AssertionError``."""
    load_large = 3.75  # load_large
    load_small = 0.204  # load_small
    with pytest.raises(AssertionError, match="Need at least one load point"):
        layopt.make_pattern_loads(
            nodal_coords, [], load_large, load_small, load_direction_default
        )


# stress limits for tests
stress_tensile = 1
stress_compressive = 1


@pytest.mark.parametrize(
    "all_patterns, active_load_cases, expected_converge",
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
            ],
            [1, 1, 1, 1],  # all load cases active
            True,
            id="All active load cases",
        ),
    ],
)
def test_stop_primal_violation_active_convergence(
    nodal_coords, c_n, areas, all_patterns, active_load_cases, dof, expected_converge
):
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
