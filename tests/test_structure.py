"""Tests for the structure module."""

from typing import Any

import numpy as np
import numpy.typing as npt
import pytest
from shapely.geometry import Polygon

from layopt import structure


@pytest.mark.parametrize(
    ("bounding_coordinates", "expected"),
    [
        pytest.param(
            np.asarray([[0, 0], [0, 1], [1, 0], [1, 1]]),
            Polygon([[0, 0], [0, 1], [1, 0], [1, 1]]),
            id="basic square",
        ),
        pytest.param(
            np.asarray([[0, 0], [0, 1], [1, 0]]),
            Polygon([[0, 0], [0, 1], [1, 0]]),
            id="basic triangle",
        ),
    ],
)
def test_make_polygon(
    bounding_coordinates: npt.NDArray[np.int32], expected: Polygon
) -> None:
    """Test for ``structure.make_polygon()``."""
    assert structure.make_polygon(bounding_coordinates) == expected


@pytest.mark.parametrize(
    ("width", "height", "polygon", "expected"),
    [
        pytest.param(
            4,
            4,
            Polygon([[0, 0], [0, 4], [4, 0], [4, 4]]),
            np.asarray(
                [
                    [0.0, 0.0],
                    [4.0, 0.0],
                    [0.0, 1.0],
                    [1.0, 1.0],
                    [3.0, 1.0],
                    [4.0, 1.0],
                    [0.0, 2.0],
                    [1.0, 2.0],
                    [2.0, 2.0],
                    [3.0, 2.0],
                    [4.0, 2.0],
                    [0.0, 3.0],
                    [1.0, 3.0],
                    [3.0, 3.0],
                    [4.0, 3.0],
                    [0.0, 4.0],
                    [4.0, 4.0],
                ]
            ),
            id="simple 4x4 square",
        ),
    ],
)
def test_create_nodes(
    width: int,
    height: int,
    polygon: Polygon,
    expected: npt.NDArray[np.float64],
) -> None:
    """Test for ``structure.create_nodes()``."""
    np.testing.assert_array_almost_equal(
        structure.create_nodes(width, height, polygon), expected
    )


@pytest.mark.parametrize(
    ("width", "height", "expected"),
    [
        pytest.param(4, 4, np.asarray([[4.0, 2.0]]), id="simple 4x4 square"),
    ],
)
def test_calc_default_loaded_points(
    width: int, height: int, expected: npt.NDArray[np.float64]
) -> None:
    """Test for ``structure.calc_loaded_points()``."""
    np.testing.assert_array_equal(
        structure.calc_default_loaded_points(width, height), expected
    )


@pytest.mark.parametrize(
    ("nodal_coords", "support_points", "expected"),
    [
        pytest.param(
            np.asarray(
                [
                    [0, 0],
                    [0, 1],
                    [1, 0],
                    [1, 1],
                ]
            ),
            np.asarray([]),
            np.asarray([0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0]),
            id="simple 1x1 square, no support points defined",
        ),
        pytest.param(
            np.asarray(
                [
                    [0, 0],
                    [0, 1],
                    [0, 2],
                    [1, 0],
                    [1, 1],
                    [1, 2],
                ]
            ),
            np.asarray([]),
            np.asarray([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]),
            id="simple 2x3 rectangle, no support points defined",
        ),
        pytest.param(
            np.asarray(
                [
                    [0, 0],
                    [0, 1],
                    [0, 2],
                    [1, 0],
                    [1, 1],
                    [1, 2],
                ]
            ),
            np.asarray([[0, 0], [0, 2]]),
            np.asarray([0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]),
            id="simple 2x3 rectangle, two support points defined",
        ),
    ],
)
def test_support_conditions(
    nodal_coords: npt.NDArray[np.int64],
    support_points: npt.NDArray[np.int64],
    expected: npt.NDArray[np.int64],
) -> None:
    """Test for ``structure.support_conditions()``."""
    np.testing.assert_array_equal(
        structure.support_conditions(
            nodal_coords=nodal_coords, support_points=support_points
        ),
        expected,
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
)
def test_make_pattern_loads_num_load_patterns(
    nodes: npt.NDArray[np.float64],
    load_large: float,
    load_small: float,
    load_direction_default: tuple[float, float],
    loaded_points: npt.NDArray[np.float64],
    expected_pattern_count: int,
):
    """Test for ``structure.make_pattern_loads()``."""
    all_patterns, _, _ = structure.make_pattern_loads(
        nodes, loaded_points, load_large, load_small, load_direction_default
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
    nodes: npt.NDArray[np.float64],
    load_large: float,
    load_small: float,
    loaded_points: npt.NDArray[np.float64],
    direction: tuple[float, float],
    expected_pattern_count: int,
    expected_patterns: npt.NDArray[np.float64],
    expected_pattern_description: list[str],
):
    """Test vertical loads, horizontal loads, and snapping to nearest nodes."""
    all_patterns, base_load, pattern_description = structure.make_pattern_loads(
        nodes, loaded_points, load_large, load_small, direction
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
    nodes: npt.NDArray[np.float64],
    loaded_points: Any,
    error: str,
    msg: str,
):
    """Test that 0 load points raises AssertionError from ``structure.make_pattern_loads()``."""
    with pytest.raises(error, match=msg):
        structure.make_pattern_loads(
            nodal_coords=nodes,
            loaded_points=loaded_points,
            load_large=3.75,
            load_small=0.204,
            load_direction=(0.0, -1.0),
        )


@pytest.mark.parametrize(
    ("nodes", "max_length", "joint_cost", "convex", "polygon", "expected"),
    [
        pytest.param(
            np.asarray([[0, 0], [0, 1], [1, 0], [1, 1]]),
            1,
            0.6,
            False,
            Polygon(np.asarray([[0, 0], [0, 1], [1, 0], [1, 1]])),
            np.asarray(
                [
                    [0.0, 1.0, 1.0, 1.0],
                    [0.0, 3.0, 1.4142135623730951, 1.0],
                    [1.0, 2.0, 1.4142135623730951, 1.0],
                    [2.0, 3.0, 1.0, 1.0],
                ]
            ),
            id="Basic square",
        ),
        pytest.param(
            np.asarray([[0, 0], [0, 1], [1, 0]]),
            1,
            0.6,
            False,
            Polygon(np.asarray([[0, 0], [0, 1], [1, 0]])),
            np.asarray(
                [
                    [0.0, 1.0, 1.0, 1.0],
                    [0.0, 2.0, 1.0, 1.0],
                    [1.0, 2.0, 1.4142135623730951, 1.0],
                ]
            ),
            id="Basic triangle",
        ),
    ],
)
def test_calc_potential_members(
    nodes: npt.NDArray[np.int64],
    max_length: float,
    joint_cost: float,
    convex: bool,
    polygon: Polygon,
    expected: npt.NDArray,
) -> None:
    """Test for ``structure.calc_potential_members()``."""
    np.testing.assert_array_equal(
        structure.calc_potential_members(
            nodes=nodes,
            max_length=max_length,
            joint_cost=joint_cost,
            convex=convex,
            polygon=polygon,
        ),
        expected,
    )


@pytest.mark.parametrize(
    (
        "primal_method",
        "all_patterns_length",
        "expected_primal_method",
        "expected_active_load_cases",
    ),
    [
        pytest.param(
            "residual", 4, True, np.asarray([1, 0, 0, 0]), id="residual of length 4"
        ),
        pytest.param(
            "load_factor",
            4,
            True,
            np.asarray([1, 0, 0, 0]),
            id="load_factor of length 4",
        ),
        pytest.param(
            "other", 4, False, np.asarray([1, 1, 1, 1]), id="other of length 4"
        ),
    ],
)
def test_primal_adaptivity(
    primal_method: str,
    all_patterns_length: int,
    expected_primal_method: bool,
    expected_active_load_cases: npt.NDArray[np.int32],
) -> None:
    """Test for ``structure.primal_adaptivity()``."""
    primal_method_result, active_load_cases = structure.primal_adaptivity(
        primal_method=primal_method, all_patterns_length=all_patterns_length
    )
    assert primal_method_result == expected_primal_method
    np.testing.assert_array_equal(
        active_load_cases,
        expected_active_load_cases,
    )
