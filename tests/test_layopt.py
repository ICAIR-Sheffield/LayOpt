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
            np.asarray([[3, 3]]),  # loaded_points
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
            np.asarray([[8, 0], [8, 4]]),  # loaded_points
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
            np.asarray([[3, 0], [3, 1]]),  # loaded_points
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
            np.asarray(
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
            ),  # loaded_points
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


# @pytest.mark.parametrize(
#     ("loaded_points", "expected_pattern_count"),
#     [
#         pytest.param([[0.0, 1]], 2, id="1 load point (2^1)"),
#         pytest.param([[0.0, 1], [4.0, 1]], 4, id="2 load points (2^2)"),
#         pytest.param([[0.0, 1], [2.0, 1], [4.0, 1]], 8, id="3 load points (2^3)"),
#     ],
#     ids=["1_point", "2_points", "3_points"],
# )
# def test_make_pattern_loads_num_load_patterns(
#     nodal_coords: npt.NDArray,
#     load_large: float,
#     load_small: float,
#     load_direction_default: tuple[float, float],
#     loaded_points: list,
#     expected_pattern_count: int,
# ):
#     all_patterns, _, _ = layopt.make_pattern_loads(
#         nodal_coords, loaded_points, load_large, load_small, load_direction_default
#     )
#     assert len(all_patterns) == expected_pattern_count


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
