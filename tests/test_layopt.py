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
            "trussopt_param_one_by_one",
            id="1x1",
        ),
        pytest.param(
            "trussopt_param_two_by_two",
            id="2x2",
        ),
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
def test_testname(
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
