"""Layopt module."""

# below line for use in Colab
# @title { vertical-output: true}

## AF WIP 20260217

# -*- coding: utf-8 -*-
## This file forms supplementary material to the paper
## "Adaptive topology optimization of fail-safe truss structures" by
## Helen E. Fairclough Â· Linwei He Â· Tekle B. Asfaha Â· Sam Rigby

## This code has been developed based on the code of
## He, L., Gilbert, M. & Song, X. A Python script for adaptive layout
## optimization of trusses. Struct Multidisc Optim 60, 835â€“847 (2019).
## https://doi.org/10.1007/s00158-019-02226-6
# !pip install mosek

import csv
import itertools
import time
from math import ceil, gcd, isinf
from pathlib import Path

# import mosek.fusion as mosek
import cvxpy as cvx
import numpy as np
import numpy.typing as npt
import pandas as pd
from loguru import logger
from scipy import sparse

# from numpy.matlib import repmat
from shapely.geometry import LineString, Point, Polygon

from layopt.io import dict_to_df, get_date_time
from layopt.plotting import plot_truss

# pylint: disable=too-many-lines


def calc_eq_matrix_b(
    nodal_coords: npt.NDArray[np.float64],
    c_n: npt.NDArray[np.float64],
    dof: npt.NDArray[np.float64],
) -> sparse.coo_matrix:
    """
    Calculate equilibrium matrix B.

    Parameters
    ----------
    nodal_coords : npt.NDArray[np.float64]
        Nodal coordinates.
    c_n : npt.NDArray[np.float64]
        Active members.
    dof : npt.NDArray
        Degrees of freedom.

    Returns
    -------
    sparse.coo_matrix
        Equilibrium matrix B.
    """
    try:
        m, n1, n2 = len(c_n), c_n[:, 0].astype(int), c_n[:, 1].astype(int)
    except TypeError as e:
        msg = "Missing 'c_n'"
        raise TypeError(msg) from e

    try:
        length, x, y = (
            c_n[:, 2],
            nodal_coords[n2, 0] - nodal_coords[n1, 0],
            nodal_coords[n2, 1] - nodal_coords[n1, 1],
        )
    except IndexError as e:
        msg = f"{nodal_coords.shape=}, expected (2,{c_n.shape[1]})"
        raise IndexError(msg) from e
    except TypeError as e:
        msg = "Missing 'nodal_coords'"
        raise TypeError(msg) from e

    try:
        d0, d1, d2, d3 = dof[n1 * 2], dof[n1 * 2 + 1], dof[n2 * 2], dof[n2 * 2 + 1]
    except IndexError as e:
        msg = f"{dof.shape=}, expected ({(c_n.shape[0],)})"
        raise IndexError(msg) from e
    except TypeError as e:
        msg = "Missing 'dof'"
        raise TypeError(msg) from e

    s = np.concatenate(
        (-x / length * d0, -y / length * d1, x / length * d2, y / length * d3)
    )
    row_id = np.concatenate((n1 * 2, n1 * 2 + 1, n2 * 2, n2 * 2 + 1))
    col_id = np.concatenate((np.arange(m), np.arange(m), np.arange(m), np.arange(m)))
    return sparse.coo_matrix((s, (row_id, col_id)), shape=(len(nodal_coords) * 2, m))


def solve(
    nodal_coords: npt.NDArray[np.float64],
    c_n: npt.NDArray[np.float64],
    f: list[npt.NDArray[np.float64]],
    dof: npt.NDArray[np.float64],
    stress_tensile: float,
    stress_compressive: float,
    joint_cost: float,
) -> tuple[
    float,
    npt.NDArray[np.float64],
    list[npt.NDArray[np.float64]],
    list[npt.NDArray[np.float64]],
]:
    """
    Solve linear programming problem with given connections and pattern load cases.

    Parameters
    ----------
    nodal_coords : npt.NDArray[np.float64]
        Nodal coordinates.
    c_n : npt.NDArray[np.float64]
        Active members.
    f : list[npt.NDArray[np.float64]]
        Load cases.
    dof : npt.NDArray
        Degrees of freedom.
    stress_tensile : float
        Tensile stress limit.
    stress_compressive : float
        Compressive stress limit.
    joint_cost : float
        Joint cost.

    Returns
    -------
    tuple[float, npt.NDArray[np.float64], list[npt.NDArray[np.float64]], list[npt.NDArray[np.float64]]]
        A tuple consisting of ``volume`` (the volume of the solved problem),
        ``area`` (member areas), ``forces`` (member forces) and ``deflections``
        (virtual deflections at degrees of freedom).
    """
    member_cost = [col[2] + joint_cost for col in c_n]
    eq_matrix_b = calc_eq_matrix_b(nodal_coords, c_n, dof)
    eq_matrix_b = sparse.coo_matrix(
        (eq_matrix_b.data, (eq_matrix_b.row, eq_matrix_b.col)),
        shape=eq_matrix_b.shape,
    )

    n_members = len(c_n)
    a = cvx.Variable(n_members, nonneg=True, name="a")

    q_vars = []
    eq_constraints = []
    other_constraints = []
    for fk in f:
        qi = cvx.Variable(n_members, name="q")
        q_vars.append(qi)
        eq_con = eq_matrix_b @ qi == fk * dof
        eq_constraints.append(eq_con)
        other_constraints += [
            # eq_matrix_b @ qi == fk * dof,                          # equilibrium
            qi <= stress_compressive * a,  # compression limit
            qi >= -stress_tensile * a,  # tension limit
        ]

    objective = cvx.Minimize(member_cost @ a)
    problem = cvx.Problem(objective, eq_constraints + other_constraints)
    # uses CVXPY preference order of solvers, MOSEK first if installed
    problem.solve()

    vol = problem.value if problem.value is not None else 0.0
    a_val = a.value if a.value is not None else np.zeros(n_members)
    q_vals = [
        qi.value if qi.value is not None else np.zeros(n_members) for qi in q_vars
    ]

    # eq_constraints = constraints[::3]  # every third constraint is the equilibrium one
    u = []
    for eq_con in eq_constraints:
        dual = eq_con.dual_value
        if dual is None:
            dual = np.zeros(eq_matrix_b.shape[0])
        u.append(np.array(dual))

    if vol == 0:
        u = [ui * 10000 for ui in u]

    return vol, a_val, q_vals, u


def stop_violation(
    nodal_coords: npt.NDArray[np.float64],
    potential_members: npt.NDArray[np.float64],
    dof: npt.NDArray[np.float64],
    stress_tensile: float,
    stress_compressive: float,
    deflections: list[npt.NDArray[np.float64]],
    joint_cost: float,
) -> int:
    """
    Check for dual violation and add new members.

    Parameters
    ----------
    nodal_coords : npt.NDArray[np.float64]
        Nodal coordinates.
    potential_members : npt.NDArray[np.float64]
        A list of all possible members.
    dof : npt.NDArray[np.float64]
        Degrees of freedom.
    stress_tensile : float
        Tensile stress limit.
    stress_compressive : float
        Compressive stress limit.
    deflections : list[npt.NDArray[np.float64]]
        Virtual deflections at degrees of freedom.
    joint_cost : float
        Joint cost.

    Returns
    -------
    int
        Number of members added.
    """
    lst = np.where(potential_members[:, 3] == False)[0]  # noqa: E712, pylint: disable=singleton-comparison
    c_n = potential_members[lst]
    member_cost = c_n[:, 2] + joint_cost
    eq_matrix_b = calc_eq_matrix_b(nodal_coords, c_n, dof).tocsc()
    y = np.zeros(len(c_n))
    for uk in deflections:
        yk = np.multiply(
            eq_matrix_b.transpose().dot(uk) / member_cost,
            np.array([[stress_tensile], [-stress_compressive]]),
        )
        y += np.amax(yk, axis=0)
    vio_c_n = np.where(y > 1.000)[0]
    vio_sort = np.flipud(np.argsort(y[vio_c_n]))
    num = ceil(0.1 * (len(potential_members) - len(c_n)))  # size of existing problem
    for i in range(min(num, len(vio_sort))):
        potential_members[lst[vio_c_n[vio_sort[i]]]][3] = True  # set member as active
    return min(num, len(vio_sort))


def make_pattern_loads(
    nodal_coords: npt.NDArray[np.float64],
    loaded_points: npt.NDArray[np.int64],
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


# ns-rse 2026-03-23 : Could this comment perhaps form the extended description for the function?
# add new pattern load cases primal violation
# violation criterion: check if min over active j of ||B*q[j] - f[k]*dof|| > tol
# (essentially checking if Bq-f=0)
# for each inactive load pattern, check whether any existing active solution
# q[j] already satisfies equilibrium for that load pattern. if not, pattern
# is violated and is added
def stop_primal_violation_residual(
    nodal_coords: npt.NDArray[np.float64],
    c_n: npt.NDArray[np.float64],
    forces: npt.NDArray[np.float64],
    all_patterns: list[npt.NDArray[np.float64]],
    active_load_cases: npt.NDArray[np.int64],
    dof: npt.NDArray[np.float64],
) -> bool:
    """
    Check for primal violation (equilibrium constraint violation) and add new load cases.

    Parameters
    ----------
    nodal_coords : npt.NDArray
        Nodal coordinates.
    c_n : npt.NDArray
        Active members.
    forces : list
        Member forces.
    all_patterns : list[npt.NDArray[np.float64]]
        All load cases.
    active_load_cases : npt.NDArray[np.int64]
        For each load case, bool set to ``True`` if active, ``False`` otherwise.
    dof : npt.NDArray[np.float64]
        Degrees of freedom.

    Returns
    -------
    bool
        True if converged and no load cases added.
    """
    tol = 1e-5
    eq_matrix_b = calc_eq_matrix_b(nodal_coords, c_n, dof).tocsc()

    total_violation = np.zeros(len(all_patterns))

    # loop through all (active and inactive) pattern load cases
    for k, _ in enumerate(all_patterns):
        if active_load_cases[k] == 1:
            continue  # skip active cases

        fk_dof = all_patterns[k] * dof
        residuals = [
            np.linalg.norm(eq_matrix_b.dot(force) - fk_dof) for force in forces
        ]

        # find min of residuals over active pattern load cases
        total_violation[k] = min(residuals)

    violated = (
        total_violation > tol
    )  # true if there are violated cases need to be added
    n_to_add = max(1, ceil(len(all_patterns) / 10))  # limit on num to add

    if any(violated):
        # ns-rse 2026-03-17 : extract sorting violations to its own function
        # Sort by violation severity
        by_violation = sorted(
            [i for i in range(len(total_violation)) if total_violation[i] > tol],
            key=lambda k: total_violation[k],
            reverse=True,
        )

        if len(by_violation) == 0:
            return True

        # Active most violated load pattern
        active_load_cases[by_violation[0]] = 1
        violations_added_this_iter = [by_violation[0]]
        by_violation.pop(0)

        # Add distinct cases
        # distinct if violated load pattern vector (after normalisation)
        # is not parallel to added load pattern vector (after normalisation)
        # (with current loading everything should be distinct?)
        for _ in range(n_to_add - 1):
            if len(by_violation) == 0:
                break
            added_case = False
            for k in by_violation:
                fk = all_patterns[k]
                fk_norm = fk / (np.linalg.norm(fk) + 1e-12)
                distinct = True
                for j in violations_added_this_iter:
                    fj = all_patterns[j]
                    fj_norm = fj / (np.linalg.norm(fj) + 1e-12)
                    if np.dot(fk_norm, fj_norm) > 0.99:
                        distinct = False
                        break
                if distinct:
                    active_load_cases[k] = 1
                    violations_added_this_iter.append(k)
                    by_violation.remove(k)
                    added_case = True
                    break
            if not added_case:
                break

        return False  # cases added, keep going
    return True  # converged, terminate


# for each inactive load pattern f[k], solve an LP to find the maximum
# load factor lambda that the current design (with fixed member areas a) can carry:
#    maximize lambda
#    subject to:
#        B*q = lambda*f[k]        (equilibrium with scaled load)
#        -sigma_c*a <= q <= sigma_t*a  (stress limits with fixed areas)
# violation criterion: check if lambda >= 1
# if so, structure can carry full load so no violation
# else structure can only carry some of the load, violation, so add load case
def stop_primal_violation_pattern(
    nodal_coords: npt.NDArray[np.float64],
    c_n: npt.NDArray[np.float64],
    areas: npt.NDArray[np.float64],
    all_patterns: list[npt.NDArray[np.float64]],
    active_load_cases: npt.NDArray[np.int64],
    dof: npt.NDArray[np.float64],
    stress_tensile: float,
    stress_compressive: float,
) -> bool:
    """
    Check for primal violation (load factor structural analysis) and add new load cases.

    Parameters
    ----------
    nodal_coords : npt.NDArray[np.float64]
        Nodal coordinates.
    c_n : npt.NDArray[np.float64]
        Active members.
    areas : list[npt.NDArray[np.float64]]
        Member areas.
    all_patterns : list[npt.NDArray[np.float64]]
        All load cases.
    active_load_cases : npt.NDArray[np.int64]
        For each load case, bool set to True if active, False otherwise.
    dof : npt.NDArray
        Degrees of freedom.
    stress_tensile : float
        Tensile stress limit.
    stress_compressive : float
        Compressive stress limit.

    Returns
    -------
    bool
        ``True`` if converged and no load cases added.
    """
    tol = 0.99  # lambda must be >= 1 to be considered feasible
    area_tol = 1e-8  # members with area below this are treated as having zero area

    # Filter out zero area members
    nonzero_areas_bool = np.asarray(areas) > area_tol
    c_n_nonzero = c_n[nonzero_areas_bool]
    areas_nonzero = np.asarray(areas)[nonzero_areas_bool]

    eq_matrix_b = calc_eq_matrix_b(nodal_coords, c_n_nonzero, dof)
    eq_matrix_b = sparse.coo_matrix(
        (eq_matrix_b.data, (eq_matrix_b.row, eq_matrix_b.col)),
        shape=eq_matrix_b.shape,
    )

    n_members = len(c_n_nonzero)
    n_dof = eq_matrix_b.shape[0]
    load_factors = np.ones(len(all_patterns))  # lambda=1 for active cases

    q_var = cvx.Variable(n_members, name="q")
    lambda_var = cvx.Variable(nonneg=True, name="lambda")

    fk_dof_param = cvx.Parameter(n_dof, name="fk_dof")

    constraints = [
        eq_matrix_b @ q_var == lambda_var * fk_dof_param,  # equilibrium
        q_var <= stress_compressive * areas_nonzero,  # compression limit
        q_var >= -stress_tensile * areas_nonzero,  # tension limit
    ]
    objective = cvx.Maximize(lambda_var)
    problem = cvx.Problem(objective, constraints)

    # loop through all (active and inactive) pattern load cases
    for k, pattern in enumerate(all_patterns):
        if active_load_cases[k] == 1:
            continue  # skip active cases

        fk_dof_param.value = pattern * dof

        # uses CVXPY preference order of solvers, MOSEK first if installed
        problem.solve()

        load_factors[k] = lambda_var.value if lambda_var.value is not None else 0.0

    # Violation: load factor < 1 (with tolerance)
    violated = load_factors < tol
    n_to_add = max(1, ceil(len(all_patterns) / 10))

    if any(violated):  # pylint: disable=too-many-nested-blocks
        # ns-rse 2026-03-17 : extract sorting violations to its own function
        # Sort by severity: lowest load factor = most violated
        by_violation = sorted(
            [i for i in range(len(load_factors)) if violated[i]],
            key=lambda k: load_factors[k],
        )

        if len(by_violation) == 0:
            return True

        # Add most violated (lowest lambda)
        most_violated_id = by_violation[0]
        active_load_cases[most_violated_id] = 1
        logger.info(
            f"  Adding most violated pattern {by_violation[0]}: lambda={load_factors[most_violated_id]:.3f}"
        )
        violations_added_this_iter = [by_violation[0]]
        by_violation.pop(0)

        # Add distinct cases
        # distinct if load factor is +/-10% of added load factor
        # and if violated load pattern vector (after normalisation)
        # is not parallel to added load pattern vector (after normalisation)
        # (with current loading no load pattern vectors should be parallel?)
        for _ in range(n_to_add - 1):
            if len(by_violation) == 0:
                break
            added_case = False
            for k in by_violation:
                # check if load case k has a significantly different load factor
                # from all load cases added this iteration
                distinct = True
                for j in violations_added_this_iter:
                    # check if both load factors are approx 0, only add one if so
                    if load_factors[k] < 0.01 and load_factors[j] < 0.01:
                        distinct = False
                        break
                    # if added load factor is 0 but other violated ones aren't,
                    # other violated cases are distinct
                    if load_factors[j] < 0.01:
                        continue
                    # check ratio of load factors if neither approx 0
                    lambda_ratio = load_factors[k] / (load_factors[j] + 1e-12)
                    if 0.9 < lambda_ratio < 1.1:  # Within 10% of each other
                        distinct = False
                        break
                if distinct:
                    fk = all_patterns[k]
                    fk_norm = fk / (np.linalg.norm(fk) + 1e-12)
                    distinct = True
                    for j in violations_added_this_iter:
                        fj = all_patterns[j]
                        fj_norm = fj / (np.linalg.norm(fj) + 1e-12)
                        if np.dot(fk_norm, fj_norm) > 0.99:
                            distinct = False
                            break
                if distinct:
                    active_load_cases[k] = 1
                    logger.info(
                        f"  Adding {len(violations_added_this_iter) + 1} distinct pattern {k}: lambda={load_factors[k]:.3f}"
                    )
                    violations_added_this_iter.append(k)
                    by_violation.remove(k)
                    added_case = True
                    break
            if not added_case:
                break

        return False  # cases added, keep going
    return True  # converged, terminate


# Main function - edited for pattern loading
def trussopt(
    filter_level: float | None = None,
    width: float = 1.0,
    height: float = 1.0,
    stress_tensile: float = 1.0,
    stress_compressive: float = 1.0,
    joint_cost: float = 0.0,
    loaded_points: npt.NDArray[np.int64] | None = None,
    # ns-rse 2026-03-17 : val implies single value but its a list, perhaps load_range? dict perhaps
    load_direction: tuple[float, float] = (0.0, -1.0),
    load_large: float = 50.0,
    load_small: float = 5.0,
    max_length: float = 1000.0,
    # ns-rse 2026-03-17 : Set type hint and default to None
    support_points: npt.NDArray[np.float64] | None = None,
    member_area_filtering: float = 0.001,
    primal_method: str = "load_factor",
    problem_name: str = "None",
    # save_to_csv: bool = True,
    # csv_filename: str = "pattern_loading_results.csv",
    notes: str = "",
    output_dir: str | Path = Path("./"),
    plot: bool = False,
    bar_thickness: float = 0.3,
    dpi: int = 1200,
) -> tuple[float, dict[int, float], pd.DataFrame, float]:
    """
    Main function, perform adaptive member adding procedure with multiple load cases.

    Parameters
    ----------
    filter_level : float
        Levels to filter on.
    width : float
        Width of structure.
    height : float
        Height of structure.
    stress_tensile : float
        Tensile stress limit.
    stress_compressive : float
        Compressive stress limit.
    joint_cost : float
        Joint cost.
    loaded_points : npt.NDArray[np.int64]
        Load points (default=[]).
    load_direction : list
        Load direction (default=``(0,-1)``).
    load_large : float
        Large load to apply at each load point (default=50).
    load_small : float
        Small load to apply at each load point (default=5).
    max_length : float
        Maximum member length.
    support_points : npt.NDArray[np.float64]
        Support points (default=[]).
    member_area_filtering : float
        Fraction of maximum member area for output threshold.
    primal_method : str
        Primal violation method (default='load_factor').
    problem_name : str
        Name of problem to solve (default=``None``).
    notes : str
        Notes (default='').
    output_dir : str | Path
        Directory to save plots to.
    plot : bool
        Whether to plot the trusses.
    bar_thickness : float
        Bar thickness for plotting.
    dpi : int
        Dots per inch for plotting.

    Returns
    -------
    tuple[float, dict[int, float], pd.DataFrame, float]
        A tuple consisting of ``volume`` (the final volume of the solved problem) and ``filter_areas_dict``
        (dict with keys ground structure member indices and values corresponding
         final member areas of the solved problem),
        a dataframe of results and the ``filter_level``.
    """
    setup_start = time.process_time()
    # Make domain
    poly = Polygon([(0, 0), (width, 0), (width, height), (0, height)])
    convex = poly.convex_hull.area == poly.area
    logger.debug(f"Domain created, convex? : {convex=}")

    # Make nodes
    xv, yv = np.meshgrid(range(width + 1), range(height + 1))
    points = [Point(xv.flat[i], yv.flat[i]) for i in range(xv.size)]
    logger.debug(f"Points created : {len(points)=}")
    nodal_coords = np.array([[pt.x, pt.y] for pt in points if poly.intersects(pt)])
    logger.debug(f"Node coordinates :\n{nodal_coords=}")
    dof = np.ones((len(nodal_coords), 2))

    # Default load point
    if loaded_points is None:
        loaded_points = np.asarray([[width, height // 2]])
        logger.info(f"Loaded points not provided, calculated as : {loaded_points=}")
    # support conditions
    for i, node in enumerate(nodal_coords):
        if support_points.size == 0:  # type: ignore[union-attr]
            if node[0] == 0:
                dof[i, :] = [0, 0]  # Support nodes with x=0
        else:
            dof[i, :] = (
                [0, 0]
                if any((node == point).all() for point in support_points)
                else [1, 1]
            )
    logger.debug(f"Degrees of Freedom : {dof=}")
    dof = np.array(dof).flatten()

    # Generate all pattern loads
    # ns-rse 2026-03-17 : Unused arguments but may combine all_patterns and pattern_descriptions to dict
    # all_patterns, base_load, pattern_descriptions = make_pattern_loads(
    all_patterns, _, _ = make_pattern_loads(
        nodal_coords, loaded_points, load_large, load_small, load_direction
    )

    # Create the 'ground structure'
    _potential_members = []
    for i, j in itertools.combinations(range(len(nodal_coords)), 2):
        dx, dy = (
            abs(nodal_coords[i][0] - nodal_coords[j][0]),
            abs(nodal_coords[i][1] - nodal_coords[j][1]),
        )
        length = np.sqrt(dx**2 + dy**2)
        # Remove overlapping members, or members longer than maxLength
        if (length < max_length and gcd(int(dx), int(dy)) == 1) or joint_cost != 0:
            seg = [] if convex else LineString([nodal_coords[i], nodal_coords[j]])
            if convex or poly.contains(seg) or poly.boundary.contains(seg):
                _potential_members.append([i, j, length, False])
    potential_members = np.array(_potential_members)

    # Create the active members
    # DualAdaptivity = True
    # start_len = 1.5 if DualAdaptivity else 10000
    # for pm in [p for p in PML if p[2] <= start_len]:  # Activate short members (adaptive)
    # ns-rse 2026-03-16 : DualAdaptivity is always 'True'
    for pm in [
        p for p in potential_members if p[2] <= 1.5
    ]:  # Activate short members (adaptive)
        pm[3] = True

    #### Primal adaptivity: start with base load case only ####
    primal_adaptivity = True
    # if PrimalAdaptivity:
    #     activeLoadCases = np.zeros(len(allPatterns), dtype=int)
    #     activeLoadCases[0] = 1  # Base case = all large loads
    # # does below make sense here?
    # else:
    #     activeLoadCases = np.ones(len(allPatterns), dtype=int)
    if primal_method in {"residual", "load_factor"}:
        primal_adaptivity = True
        active_load_cases = np.zeros(len(all_patterns), dtype=int)
        active_load_cases[0] = 1  # Base case = all large loads
    else:
        primal_adaptivity = False
        active_load_cases = np.ones(len(all_patterns), dtype=int)

    setup_end = time.process_time()
    logger.info(f"Setup took {setup_end - setup_start!s}")
    logger.info(f"    Nodes               : {len(nodal_coords)}")
    logger.info(f"    Members             : {len(potential_members)}")
    logger.info(f"    Total load patterns : {len(all_patterns)}")

    vol = 1e9  # arbitrary large number to initialise
    # Start the 'member adding' loop
    for itr in range(1, 100):
        last_volume = vol
        # Get active members/parts of matrices
        c_n = potential_members[potential_members[:, 3] == True]  # noqa: E712, pylint: disable=singleton-comparison

        # Get active pattern loads
        f_active = [
            all_patterns[k]
            for k in range(len(all_patterns))
            if active_load_cases[k] == 1
        ]

        # solve current reduced problem
        vol, filter_areas, filter_forces, u = solve(
            nodal_coords,
            c_n,
            f_active,
            dof,
            stress_tensile,
            stress_compressive,
            joint_cost,
        )
        # We need to solve once so that we have valid values for `filter_areas ` which we then filter based on `fitler_level[s]`
        # (rename to `filter_level` but need to check first if that is what we want to parallelise on or if it is
        # `primal_method`).

        # output
        if isinf(vol):
            logger.error("Infeasible problem detected")
            return [], [], [], []
        n_active = int(np.sum(active_load_cases))
        # ns-rse 2026-03-23 : Could this perhaps be debugging?
        logger.info(
            f"Iteration: {itr}, vol: {vol}, mems: {len(c_n)} active load cases:{n_active}/{len(all_patterns)}"
        )
        # plot interim solutions (slow)
        # plotTruss(nodal_coords, c_n, a, q, max(a) * 1e-2, "Itr:" + str(itr), extraPlot = activeDamageDef)

        # inner loop - adding of members based on dual violation
        # still need PMLcache? currently unused
        # PMLcache = np.copy(PML[:,3])
        n_added = stop_violation(
            nodal_coords,
            potential_members,
            dof,
            stress_tensile,
            stress_compressive,
            u,
            joint_cost,
        )
        if not (0.99 * last_volume) < vol < (1.0001 * last_volume):
            continue  # small vol decrease = member adding close to convergence

        # outer loop - adding of pattern load cases based on primal violation
        # if stopPrimalViolationPattern(nodal_coords, c_n, a, all_patterns, active_load_cases, dof, st, sc):
        #     if numAdded > 0: # only fully terminate when no members violate
        #         continue
        #     else:
        #         break

        if primal_adaptivity:
            if primal_method == "residual":
                # Use equilibrium residual check
                converged = stop_primal_violation_residual(
                    nodal_coords,
                    c_n,
                    filter_forces,
                    all_patterns,
                    active_load_cases,
                    dof,
                )
            elif primal_method == "load_factor":
                # Use load factor LP
                converged = stop_primal_violation_pattern(
                    nodal_coords,
                    c_n,
                    filter_areas,
                    all_patterns,
                    active_load_cases,
                    dof,
                    stress_tensile,
                    stress_compressive,
                )
            # ns-rse 2026-03-17 : leaves scope for 'converged' to not be assigned if `primal_method` never matches

            if not converged:  # pylint: disable=possibly-used-before-assignment
                continue  # Cases added, keep iterating
            if n_added > 0:
                continue  # No cases added but members added
            break  # Both converged
        # No primal adaptivity - just check member convergence
        if n_added == 0:
            break  # Converged

    final_vol = vol
    logger.info(f"Volume (filter_level = 1.0): {final_vol}")
    solve_end = time.process_time()
    logger.info("Solve took " + str(solve_end - setup_end))
    logger.info(
        f"Active patterns: {int(np.sum(active_load_cases))}/{len(all_patterns)}"
    )
    # If we want to filter (i.e. filter_level != 1.0) then we must solve again using the reduced subset.
    if filter_level != 1.0:
        logger.info(f"Solving for filter level : {filter_level}")
        keep = [area > (filter_level * max(filter_areas)) for area in filter_areas]
        c_n = c_n[keep]
        final_vol, filter_areas, filter_forces, u = solve(
            nodal_coords,
            c_n,
            f_active,
            dof,
            stress_tensile,
            stress_compressive,
            joint_cost,
        )
        logger.info(f"Volume (filter_level = {filter_level}): {final_vol}")
    # Build dictionary of results
    results = {
        "timestamp": get_date_time(),
        "problem_name": problem_name or f"w{width}_h{height}_n{len(loaded_points)}",
        "filter_level": filter_level,
        "width": width,
        "height": height,
        "n_load_points": len(loaded_points),
        "n_patterns_total": len(all_patterns),
        "n_patterns_active": int(np.sum(active_load_cases)),
        "load_large": load_large,
        "load_small": load_small,
        "iterations": itr,
        "final_volume": final_vol,
        "n_members_final": len(c_n),
        "n_nodes": len(nodal_coords),
        "n_ground_structure": len(potential_members),
        "cpu_time_setup": setup_end - setup_start,
        "cpu_time_solve": solve_end - setup_end,
        "primal_method": primal_method,
        "notes": notes,
    }

    # Plot results
    if plot:
        multiplier = 1.0 if filter_level is None else filter_level
        outfile = Path(output_dir) / (
            problem_name.replace(" ", "_")
            + f"_w{width}_h{height}_n{len(loaded_points)}_filter{int(multiplier * 100)}"
        )
        if vol > 0:
            _, _ = plot_truss(
                nodal_coords=nodal_coords,
                c_n=c_n,
                areas=filter_areas,
                forces=filter_forces,
                threshold=max(filter_areas) * member_area_filtering,
                title="Filtered " + str(100 * multiplier) + "%",
                bar_thickness=bar_thickness,
                dpi=dpi,
                outfile=outfile,
            )
        else:
            logger.warning("No plot generated as volume <= 0.0")
    logger.info(f"Plotting took {time.process_time() - solve_end!s}")

    # Filter output members by area threshold
    # Build area dict where keys are ground structure member indices
    active_indices = np.where(potential_members[:, 3])[0]
    threshold = max(filter_areas) * member_area_filtering
    keep = filter_areas >= threshold
    kept_indices = active_indices[keep]
    c_n = c_n[keep]
    filter_areas_dict: dict[int, float] = {
        int(idx): float(area)
        for idx, area in zip(kept_indices, filter_areas[keep], strict=True)
    }
    logger.info(
        f"Area filtering at {member_area_filtering} ({100 * member_area_filtering}% of max): "
        f"{int(np.sum(keep))} members retained"
    )

    return vol, filter_areas_dict, dict_to_df(results), filter_level


def save_results_to_csv(
    results: dict[str, str | int | float], filename: str = "pattern_loading_results.csv"
) -> None:
    """
    Save optimization results to CSV file.

    Creates file with header if it doesn't exist, otherwise appends.

    Parameters
    ----------
    results : dict
        Dictionary containing results to save. Should include keys:
        - timestamp
        - problem_name
        - width, height
        - n_load_points
        - n_patterns_total
        - n_patterns_active
        - load_large
        - load_small
        - iterations
        - final_volume
        - n_members_final
        - n_nodes
        - n_ground_structure
        - cpu_time_setup
        - cpu_time_solve
        - primal_method
        - notes
    filename : str
        CSV filename (default=``pattern_loading_results.csv``).
    """
    file_exists = Path(filename).is_file()

    # Define column order
    fieldnames = [
        "timestamp",
        "problem_name",
        "width",
        "height",
        "n_load_points",
        "n_patterns_total",
        "n_patterns_active",
        "load_large",
        "load_small",
        "iterations",
        "final_volume",
        "n_members_final",
        "n_nodes",
        "n_ground_structure",
        "cpu_time_setup",
        "cpu_time_solve",
        # 'cpu_time_total',
        # 'wall_time_total',
        "primal_method",
        "notes",
    ]

    with Path(filename).open("a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write header if new file
        if not file_exists:
            writer.writeheader()

        # Write data
        writer.writerow(results)

    logger.info(f"\nResults saved to {filename}")


# # Example usage:
# if __name__ == "__main__":
#     # Test the function
#     test_results = {
#         'timestamp': '2026-03-04 15:30:00',
#         'problem_name': 'test_problem',
#         'width': 8,
#         'height': 8,
#         'n_load_points': 2,
#         'n_patterns_total': 4,
#         'n_patterns_active': 3,
#         'load_large': 50,
#         'load_small': 5,
#         'iterations': 12,
#         'final_volume': 123.456,
#         'n_members_final': 87,
#         'n_nodes': 81,
#         'n_ground_structure': 1234,
#         'cpu_time_setup': 0.234,
#         'cpu_time_solve': 12.456,
#         'cpu_time_total': 15.813,
#         'wall_time_total': 17.509,
#         'primal_adaptive': True,
#         'notes': 'Test run'
#     }

#     save_results_to_csv(test_results, 'test_results.csv')
#     print("Test completed - check test_results.csv")
