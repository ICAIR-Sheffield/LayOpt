"""Functions for creating structure components."""

import itertools
from math import gcd

import numpy as np
import numpy.typing as npt
from loguru import logger
from shapely.geometry import LineString, Point, Polygon


def make_polygon(bounding_coordinates: npt.NDArray[np.int32]) -> Polygon:
    """
    Construct a ``Polygon`` domain based on the supplied coordinates.

    Traditionally these are rectangular or square but there is no reason that the array of points can not be any other
    shape.

    Parameters
    ----------
    bounding_coordinates : npt.NDArray[np.int32]
        Coordinates that bound the structure.

    Returns
    -------
    Polygon
        A ``Polygon`` object (from the shapely package).
    """
    return Polygon(bounding_coordinates)


def create_nodes(width: int, height: int, polygon: Polygon) -> npt.NDArray[np.float64]:
    """
    Create the nodes for the structure.

    Parameters
    ----------
    width : int | float
        The width of the structure.
    height : int | float
        The height of the structure.
    polygon : Polygon
        Polygon of the structure.

    Returns
    -------
    npt.NDArray[np.float64]
        Two dimensional array of node coordinates.
    """
    xv, yv = np.meshgrid(range(width + 1), range(height + 1))
    points = [Point(xv.flat[i], yv.flat[i]) for i in range(xv.size)]
    logger.debug(f"Points created : {len(points)=}")
    return np.array([[pt.x, pt.y] for pt in points if polygon.intersects(pt)])


def calc_default_loaded_points(width: int, height: int) -> npt.NDArray[np.float64]:
    """
    Calculate loaded points based on width and height.

    Loaded points are calculated as being located at the width and mid-point of the height.

    Parameters
    ----------
    width : int
        Width of structure.
    height : int
        Height of structure.

    Returns
    -------
    npt.NDArray[np.float64]
        Array of loaded points.
    """
    return np.asarray([[width, height // 2]])


def support_conditions(
    nodal_coords: npt.NDArray[np.float64], support_points: npt.NDArray[np.float64]
) -> npt.NDArray[np.float64]:
    """
    Create the degrees of freedom for support conditions.

    Parameters
    ----------
    nodal_coords : npt.NDArray[np.float64]
        Coordinates for all nodes.
    support_points : npt.NDArray[np.float64]
        Preselected support points.

    Returns
    -------
    npt.NDArray[np.float64]
        Flattened array of degrees of freedom.
    """
    dof = np.ones((len(nodal_coords), 2))
    for i, node in enumerate(nodal_coords):
        if support_points.size == 0:
            if node[0] == 0:
                dof[i, :] = [0, 0]  # Support nodes with x=0
        else:
            dof[i, :] = (
                [0, 0]
                if any((node == point).all() for point in support_points)
                else [1, 1]
            )
    return np.array(dof).flatten()


def make_pattern_loads(
    nodal_coords: npt.NDArray[np.float64],
    loaded_points: npt.NDArray[np.int64],  # pylint: disable=redefined-outer-name
    load_large: float = 50.0,
    load_small: float = 5.0,
    load_direction: tuple[float, float] = (0.0, -1.0),
) -> tuple[list[npt.NDArray[np.float64]], npt.NDArray[np.float64], list[str]]:
    """
    Generate all 2^n combinations of large/small loads at each load point.

    Parameters
    ----------
    nodal_coords : npt.NDArray[np.float64]
        Nodal coordinates.
    loaded_points : npt.NDArray[np.int64]
        Load points.
    load_large : float
        Large load to apply at each load point (default=``50``).
    load_small : float
        Small load to apply at each load point (default=``5``).
    load_direction : tuple[float, float]
        Load direction (default=``(0,-1)``).

    Returns
    -------
    tuple[list[npt.NDArray[np.float64]], npt.NDArray[np.float64], list[str]]
        A tuple consisting of ``all_patterns`` (all load cases), ``base_load``
        (base load case) and ``pattern_descriptions`` (description of each load
        case using ``L`` for large or ``S`` for small at each load point).
    """
    if not isinstance(loaded_points, np.ndarray):
        msg = f"'loaded_points' is not a numpy array : {type(loaded_points)=}"
        raise TypeError(msg)
    try:
        assert loaded_points.shape[1] >= 1, IndexError(
            f"Need at least one load point : {loaded_points.shape=}"
        )
    except IndexError as e:
        msg = f"Need at least one load point : {loaded_points.shape}"
        raise IndexError(msg) from e

    # Find node indices for each load point
    load_node_indices = []
    for loaded_point in loaded_points:
        dists = np.linalg.norm(nodal_coords - np.array(loaded_point), axis=1)
        load_node_indices.append(np.argmin(dists))

    # ns-rse 2026-03-17 : Could maybe use a dictionary here to link patterns and descriptions?
    all_patterns = []
    pattern_descriptions = []

    # Generate all 2^n combinations
    # First combo (all loadLarge) is base case
    for combo in itertools.product([load_large, load_small], repeat=len(loaded_points)):
        fk = np.zeros(len(nodal_coords) * 2)
        desc = []
        for pt_idx, magnitude in enumerate(combo):
            node = load_node_indices[pt_idx]
            fk[node * 2] += magnitude * load_direction[0]
            fk[node * 2 + 1] += magnitude * load_direction[1]
            desc.append(f"pt{pt_idx}={'L' if magnitude == load_large else 'S'}")

        all_patterns.append(fk)
        pattern_descriptions.append(", ".join(desc))

    # ns-rse 2026-03-17 : Return directly as part of tuple
    base_load = all_patterns[0]  # First pattern = all large loads
    logger.info(
        f"Total patterns for {len(loaded_points)} load point(s) : {len(all_patterns)}"
    )
    logger.info(f"Base case (all large) : {pattern_descriptions[0]}")
    return all_patterns, base_load, pattern_descriptions


def calc_potential_members(
    nodes: npt.NDArray[np.float64],
    max_length: float,
    joint_cost: float,
    convex: bool,
    polygon: Polygon,
    max_length_initial_ground_structure: float = 1.5,
) -> npt.NDArray[np.float64]:
    """
    Create the ground structure.

    Parameters
    ----------
    nodes : npt.NDArray[np.float64],
        Node coordinates.
    max_length : int | float,
        Maximum length.
    joint_cost : int | float,
        Joint cost.
    convex : bool,
        Whether the structure is convex.
    polygon : Polygon
        Bounding box for the structure.
    max_length_initial_ground_structure : float
        Threshold for marking a potential member as active in the initial ground structure.

    Returns
    -------
    npt.NDArray[np.float64]
        Array of node start, end, length and active status with overlapping members and members `> max_length` removed.
    """
    potential_members = []
    for i, j in itertools.combinations(range(len(nodes)), 2):
        dx, dy = (
            abs(nodes[i][0] - nodes[j][0]),
            abs(nodes[i][1] - nodes[j][1]),
        )
        length = np.sqrt(dx**2 + dy**2)
        # Remove overlapping members, or members longer than maxLength
        if (length < max_length and gcd(int(dx), int(dy)) == 1) or joint_cost != 0:
            seg = [] if convex else LineString([nodes[i], nodes[j]])
            if convex or polygon.contains(seg) or polygon.boundary.contains(seg):
                # Mark as active
                if length <= max_length_initial_ground_structure:
                    potential_members.append([i, j, length, True])
                else:
                    potential_members.append([i, j, length, False])

    return np.asarray(potential_members)


def primal_adaptivity(
    primal_method: str, all_patterns_length: int
) -> tuple[bool, npt.NDArray[np.bool]]:
    """
    Derive primal method and active load cases. Start with base load for cases only.

    Parameters
    ----------
    primal_method : str
        Primal method.
    all_patterns_length : int
        All patterns.

    Returns
    -------
    tuple[bool, npt.NDArray[np.bool]]
        A tuple of a boolean for ``primal_method`` and the associated ``active_load_cases``.
    """
    if primal_method in {"residual", "load_factor"}:
        active_load_cases = np.zeros(all_patterns_length, dtype=np.bool)
        active_load_cases[0] = 1  # Base case = all large loads
        return (True, active_load_cases)
    return (False, np.ones(all_patterns_length, dtype=np.bool))
