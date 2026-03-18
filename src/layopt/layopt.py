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
import datetime
import itertools
import time
from math import ceil, gcd, isinf
from pathlib import Path

import matplotlib.pyplot as plt
import mosek.fusion as mosek
import numpy as np
import numpy.typing as npt
from scipy import sparse

# from numpy.matlib import repmat
from shapely.geometry import LineString, Point, Polygon

plt.rcParams["figure.max_open_warning"] = 0

# pylint: disable=too-many-lines


def calc_eq_matrix_b(nodal_coords: npt.NDArray, c_n: npt.NDArray, dof: npt.NDArray):
    """
    Calculate equilibrium matrix B.

    Parameters
    ----------
    nodal_coords : npt.NDArray
        Nodal coordinates.
    c_n : npt.NDArray
        Active members.
    dof : npt.NDArray
        Degrees of freedom.

    Returns
    -------
    coo_matrix
        Equilibrium matrix B.
    """
    m, n1, n2 = len(c_n), c_n[:, 0].astype(int), c_n[:, 1].astype(int)
    l, x, y = (
        c_n[:, 2],
        nodal_coords[n2, 0] - nodal_coords[n1, 0],
        nodal_coords[n2, 1] - nodal_coords[n1, 1],
    )
    d0, d1, d2, d3 = dof[n1 * 2], dof[n1 * 2 + 1], dof[n2 * 2], dof[n2 * 2 + 1]
    # ns-rse 2026-03-18 : What are s, r and c? They are arrays but what do the elements represent?
    s = np.concatenate((-x / l * d0, -y / l * d1, x / l * d2, y / l * d3))
    r = np.concatenate((n1 * 2, n1 * 2 + 1, n2 * 2, n2 * 2 + 1))
    c = np.concatenate((np.arange(m), np.arange(m), np.arange(m), np.arange(m)))
    return sparse.coo_matrix((s, (r, c)), shape=(len(nodal_coords) * 2, m))


def solve(nodal_coords, c_n, f, dof, stress_tensile, stress_compressive, joint_cost):
    """
    Solve linear programming problem with given connections and pattern load cases.

    Parameters
    ----------
    nodal_coords : npt.NDArray
        Nodal coordinates.
    c_n : npt.NDArray
        Active members.
    f : list
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
    tuple[float, npt.NDArray, list, list]
        A tuple consisting of ``volume`` (the volume of the solved problem),
        ``area`` (member areas), ``forces`` (member forces) and ``deflections``
        (virtual deflections at degrees of freedom).
    """
    # ns-rse 2026-03-16 : What does l represent here? Is it perhaps a list of length + joint_cost so scaled length, or
    # length_cost?
    l = [col[2] + joint_cost for col in c_n]
    eq_matrix_b = calc_eq_matrix_b(nodal_coords, c_n, dof)
    q, eqn = [], []
    k = 0  # (damage+load) case number
    with mosek.Model() as model:
        a = model.variable("a", len(c_n), mosek.Domain.greaterThan(0.0))
        eq_matrix_b = mosek.Matrix.sparse(
            eq_matrix_b.shape[0],
            eq_matrix_b.shape[1],
            eq_matrix_b.row,
            eq_matrix_b.col,
            eq_matrix_b.data,
        )
        model.objective(mosek.ObjectiveSense.Minimize, mosek.Expr.dot(l, a))
        for fk in f:
            qi = model.variable(len(c_n))
            q.append(qi)
            eqni = model.constraint(
                mosek.Expr.sub(mosek.Expr.mul(eq_matrix_b, q[k]), fk * dof),
                mosek.Domain.equalsTo(0),
            )
            eqn.append(eqni)
            model.constraint(
                mosek.Expr.sub(mosek.Expr.mul(stress_compressive, a), q[k]),
                mosek.Domain.greaterThan(0),
            )
            model.constraint(
                mosek.Expr.sub(mosek.Expr.mul(-stress_tensile, a), q[k]),
                mosek.Domain.lessThan(0),
            )
            k += 1
        model.setSolverParam("optimizer", "intpnt")
        model.setSolverParam("intpntBasis", "never")
        model.acceptedSolutionStatus(mosek.AccSolutionStatus.Anything)
        # M.setLogHandler(stdout)
        model.solve()
        vol = model.primalObjValue()
        q = [np.array(qi.level()) for qi in q]
        a = a.level()
        u = [-np.array(eqnk.dual()) for eqnk in eqn]
        if vol == 0:
            u = [ui * 10000 for ui in u]

    return vol, a, q, u


def stop_violation(
    nodal_coords: npt.NDArray,
    potential_members: npt.NDArray,
    dof: npt.NDArray,
    stress_tensile: float,
    stress_compressive: float,
    deflections: list,
    joint_cost: float,
):
    """
    Check for dual violation and add new members.

    Parameters
    ----------
    nodal_coords : npt.NDArray
        Nodal coordinates.
    potential_members : npt.NDArray
        A list of all possible members.
    dof : npt.NDArray
        Degrees of freedom.
    stress_tensile : float
        Tensile stress limit.
    stress_compressive : float
        Compressive stress limit.
    deflections : list
        Virtual deflections at degrees of freedom.
    joint_cost : float
        Joint cost.

    Returns
    -------
    int
        Number of members added.
    """
    lst = np.where(potential_members[:, 3] == False)[0]  # pylint: disable=singleton-comparison
    c_n = potential_members[lst]
    # ns-rse 2026-03-17 : What is l?
    l = c_n[:, 2] + joint_cost
    eq_matrix_b = calc_eq_matrix_b(nodal_coords, c_n, dof).tocsc()
    y = np.zeros(len(c_n))
    for uk in deflections:
        yk = np.multiply(
            eq_matrix_b.transpose().dot(uk) / l,
            np.array([[stress_tensile], [-stress_compressive]]),
        )
        y += np.amax(yk, axis=0)
    vio_c_n = np.where(y > 1.000)[0]
    vio_sort = np.flipud(np.argsort(y[vio_c_n]))
    num = ceil(0.1 * (len(potential_members) - len(c_n)))  # size of existing problem
    for i in range(min(num, len(vio_sort))):
        potential_members[lst[vio_c_n[vio_sort[i]]]][3] = True  # set member as active
    return min(num, len(vio_sort))


def plot_truss(
    nodal_coords: npt.NDArray,
    c_n: npt.NDArray,
    areas: list,
    forces: list,
    threshold: float,
    title: str,
    update: bool = True,
    all_cases: bool = False,
):
    """
    Visualise truss.

    Parameters
    ----------
    nodal_coords : npt.NDArray
        Nodal coordinates.
    c_n : npt.NDArray
        Active members.
    areas : npt.NDArray
        Member areas.
    forces : list
        Member forces.
    threshold : float
        Minimum allowable member area.
    title : str
        Title for plot, typically includes the filter level expressed as a percentage.
    update : bool
        Enable interactive mode (default=``True``).
    all_cases : bool
        Plot all load cases individually (default=``False``).
    """
    if all_cases:
        plot_all_cases(
            nodal_coords=nodal_coords,
            c_n=c_n,
            areas=areas,
            forces=forces,
            threshold=threshold,
            stress_tensile=title,
        )
    else:
        fig = plt.figure()
        ax = fig.subplots()
        if update:
            plt.ion()
        else:
            plt.ioff()
        ax.axis("off")
        ax.axis("equal")
        ax.set_title(title)
        bar_thickness = 0.4  # bar thickness scale
        for i in [i for i in range(len(areas)) if areas[i] >= threshold]:
            if len(forces) > 1:  # multiple LC coloring
                if all(forces[lc][i] >= -0.001 for lc in range(len(forces))):
                    color = "r"
                elif all(forces[lc][i] <= 0.001 for lc in range(len(forces))):
                    color = "b"
                else:
                    color = "tab:gray"
            else:  # single LC coloring (black = no load, dark = less load)
                color = (
                    min(max(forces[0][i] / areas[i], 0), 1),
                    0,
                    min(max(-forces[0][i] / areas[i], 0), 1),
                )
            pos = nodal_coords[c_n[i, [0, 1]].astype(int), :]
            ax.plot(
                pos[:, 0],
                pos[:, 1],
                color=color,
                linewidth=areas[i] * bar_thickness,
                solid_capstyle="round",
            )
        if update:
            plt.pause(0.01)
        else:
            plt.show()
        # fig.savefig(st+'.pdf', dpi=1200)


def plot_all_cases(
    nodal_coords: npt.NDArray,
    c_n: npt.NDArray,
    areas: npt.NDArray,
    forces: list,
    threshold: float,
    stress_tensile: str,
) -> None:
    """
    Visualise truss, loop through all load cases and plot individually.

    Parameters
    ----------
    nodal_coords : npt.NDArray
        Nodal coordinates.
    c_n : npt.NDArray
        Active members.
    areas : npt.NDArray
        Member areas.
    forces : list
        Member forces.
    threshold : float
        Minimum allowable member area.
    stress_tensile : str
        Stress tensile in string format as a percentage.
    """
    n_cases = len(forces)
    for k in range(n_cases):
        plot_truss(
            nodal_coords=nodal_coords,
            c_n=c_n,
            areas=areas,
            forces=[forces[k]],
            threshold=threshold,
            title=stress_tensile + " case " + str(k),
            update=True,
            all_cases=False,
        )


def make_pattern_loads(
    nodal_coords: npt.NDArray,
    loaded_points: npt.NDArray,
    load_large: float = 50.0,
    load_small: float = 5.0,
    load_direction: tuple[float, float] = (0.0, -1.0),
):
    """
    Generate all 2^n combinations of large/small loads at each load point.

    Parameters
    ----------
    nodal_coords : npt.NDArray
        Nodal coordinates.
    loaded_points : npt.NDArray
        Load points.
    load_large : float
        Large load to apply at each load point (default=``50``).
    load_small : float
        Small load to apply at each load point (default=``5``).
    load_direction : tuple[float, float]
        Load direction (default=``(0,-1)``).

    Returns
    -------
    tuple[list, list, list]
        A tuple consisting of ``all_patterns`` (all load cases), ``base_load``
        (base load case) and ``pattern_descriptions`` (description of each load
        case using ``L`` for large or ``S`` for small at each load point).
    """
    n = len(loaded_points)

    # Find node indices for each load point
    load_node_indices = []
    for loaded_point in loaded_points:
        dists = np.linalg.norm(nodal_coords - np.array(loaded_point), axis=1)
        load_node_indices.append(np.argmin(dists))

    # ns-rse 2026-03-17 : Could maybe use a dictionary here to link patterns and descriptions?
    all_patterns = []
    patternodal_coordsescriptions = []

    # Generate all 2^n combinations
    # First combo (all loadLarge) is base case
    for combo in itertools.product([load_large, load_small], repeat=n):
        fk = np.zeros(len(nodal_coords) * 2)
        desc = []
        for pt_idx, magnitude in enumerate(combo):
            node = load_node_indices[pt_idx]
            fk[node * 2] += magnitude * load_direction[0]
            fk[node * 2 + 1] += magnitude * load_direction[1]
            desc.append(f"pt{pt_idx}={'L' if magnitude == load_large else 'S'}")

        all_patterns.append(fk)
        patternodal_coordsescriptions.append(", ".join(desc))

    # ns-rse 2026-03-17 : Return directly as part of tuple
    base_load = all_patterns[0]  # First pattern = all large loads

    print(f"\nPattern loading: {n} load points -> {len(all_patterns)} total patterns")
    print(f"Base case (all large): {patternodal_coordsescriptions[0]}")

    return all_patterns, base_load, patternodal_coordsescriptions


# add new pattern load cases primal violation
# violation criterion: check if min over active j of ||B*q[j] - f[k]*dof|| > tol
# (essentially checking if Bq-f=0)
# for each inactive load pattern, check whether any existing active solution
# q[j] already satisfies equilibrium for that load pattern. if not, pattern
# is violated and is added
def stop_primal_violation_residual(
    nodal_coords: npt.NDArray,
    c_n: npt.NDArray,
    forces: npt.NDArray,
    all_patterns: list,
    active_load_cases: list,
    dof: npt.NDArray,
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
    all_patterns : list
        All load cases.
    active_load_cases : list
        For each load case, bool set to ``True`` if active, ``False`` otherwise.
    dof : npt.NDArray
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
        # ns-rse 2026-03-18 : potential list compreshension
        # residuals = [np.linalg.norm(eq_matrix_b.dot(force) - fk_dof) for force in forces]
        residuals = []
        for qj in forces:
            # store ||B*q[j] - f[k]*dof||
            residual = np.linalg.norm(eq_matrix_b.dot(qj) - fk_dof)
            residuals.append(residual)

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
        # ns-rse 2026-03-17 : violations are added on this iteration, can we be more descriptive?
        added_this_iter = [by_violation[0]]
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
                for j in added_this_iter:
                    fj = all_patterns[j]
                    fj_norm = fj / (np.linalg.norm(fj) + 1e-12)
                    if np.dot(fk_norm, fj_norm) > 0.99:
                        distinct = False
                        break
                if distinct:
                    active_load_cases[k] = 1
                    added_this_iter.append(k)
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
    nodal_coords: npt.NDArray,
    c_n: npt.NDArray,
    areas: list[float],
    all_patterns: list,
    active_load_cases: list,
    dof: npt.NDArray,
    stress_tensile: float,
    stress_compressive: float,
) -> bool:
    """
    Check for primal violation (load factor structural analysis) and add new load cases.

    Parameters
    ----------
    nodal_coords : npt.NDArray
        Nodal coordinates.
    c_n : npt.NDArray
        Active members.
    areas : list[float]
        Member areas.
    all_patterns : list
        All load cases.
    active_load_cases : list
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

    eq_matrix_b = calc_eq_matrix_b(nodal_coords, c_n, dof)
    load_factors = np.ones(len(all_patterns))  # lambda=1 for active cases

    # loop through all (active and inactive) pattern load cases
    for k, _ in enumerate(all_patterns):
        if active_load_cases[k] == 1:
            continue  # skip active cases

        fk_dof = all_patterns[k] * dof

        # Solve LP: maximize lambda subject to B*q = lambda*f, -sigma*a <= q <= sigma*a
        with mosek.Model() as model:
            # Variables
            q_var = model.variable("q", len(c_n))
            lambda_var = model.variable("lambda", 1, mosek.Domain.greaterThan(0.0))

            # Objective: maximize lambda
            model.objective(mosek.ObjectiveSense.Maximize, lambda_var)

            # Constraint 1: B*q = lambda*f
            b_mosek = mosek.Matrix.sparse(
                eq_matrix_b.shape[0],
                eq_matrix_b.shape[1],
                eq_matrix_b.row,
                eq_matrix_b.col,
                eq_matrix_b.data,
            )
            model.constraint(
                mosek.Expr.sub(
                    mosek.Expr.mul(b_mosek, q_var),
                    mosek.Expr.mul(fk_dof, lambda_var.index(0)),
                ),
                mosek.Domain.equalsTo(0),
            )

            # Constraint 2: q <= sigma_t * a (tension limit)
            model.constraint(
                mosek.Expr.sub(q_var, stress_tensile * areas), mosek.Domain.lessThan(0)
            )

            # Constraint 3: q >= -sigma_c * a (compression limit)
            model.constraint(
                mosek.Expr.sub(q_var, -stress_compressive * areas),
                mosek.Domain.greaterThan(0),
            )

            # Solve
            model.setSolverParam("optimizer", "intpnt")
            model.acceptedSolutionStatus(mosek.AccSolutionStatus.Anything)
            model.solve()
            load_factors[k] = lambda_var.level()[0]

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
        print(
            f"  Adding most violated pattern {by_violation[0]}: lambda={load_factors[most_violated_id]:.3f}"
        )
        # ns-rse 2026-03-17 : violations are added on this iteration, can we be more descriptive?
        added_this_iter = [by_violation[0]]
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
                for j in added_this_iter:
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
                    for j in added_this_iter:
                        fj = all_patterns[j]
                        fj_norm = fj / (np.linalg.norm(fj) + 1e-12)
                        if np.dot(fk_norm, fj_norm) > 0.99:
                            distinct = False
                            break
                if distinct:
                    active_load_cases[k] = 1
                    print(
                        f"  Adding {len(added_this_iter) + 1} distinct pattern {k}: lambda={load_factors[k]:.3f}"
                    )
                    added_this_iter.append(k)
                    by_violation.remove(k)
                    added_case = True
                    break
            if not added_case:
                break

        return False  # cases added, keep going
    return True  # converged, terminate


# Main function - edited for pattern loading
def trussopt(
    width: float,
    height: float,
    stress_tensile: float = 1.0,
    stress_compressive: float = 1.0,
    joint_cost: float = 0.0,
    loaded_points: list | None = None,
    # ns-rse 2026-03-17 : val implies single value but its a list, perhaps load_range? dict perhaps
    load_val: tuple[float, float] = (0.0, -1.0),
    load_large: float = 50.0,  # ns-rse 2026-03-17 : load_max ?
    load_small: float = 5.0,  # ns-rse 2026-03-17 : load_min ?
    max_length=1000,
    # ns-rse 2026-03-17 : Set type hint and default to None
    support_points: list | None = None,
    filtering: bool = False,  # as boolean makes it "pythonic" to remove 'do' but what is being filered?
    primal_method: str = "load_factor",
    problem_name: str = "None",
    save_to_csv: bool = True,
    csv_filename: str = "pattern_loading_results.csv",
    notes: str = "",
):
    """
    Main function, perform adaptive member adding procedure with multiple load cases.

    Parameters
    ----------
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
    loaded_points : list
        Load points (default=[]).
    load_val : list
        Load direction (default=``(0,-1)``).
    load_large : float
        Large load to apply at each load point (default=50).
    load_small : float
        Small load to apply at each load point (default=5).
    max_length : float
        Maximum member length.
    support_points : list
        Support points (default=[]).
    filtering : bool
        Enable post-processing filtering on member areas (default=``False``).
    primal_method : str
        Primal violation method (default='load_factor').
    problem_name : str
        Name of problem to solve (default=``None``).
    save_to_csv : bool
        Enable saving results to CSV file (default=True).
    csv_filename : str
        CSV filename for saved results (default='pattern_loading_results.csv').
    notes : str
        Notes (default='').

    Returns
    -------
    tuple[float, npt.NDArray]
        A tuple consisting of ``volume`` (the final volume of the solved problem)
        and ``area`` (final member areas of the solved problem).
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    setup_start = time.process_time()

    # Make domain
    poly = Polygon([(0, 0), (width, 0), (width, height), (0, height)])
    convex = poly.convex_hull.area == poly.area

    # Make nodes
    xv, yv = np.meshgrid(range(width + 1), range(height + 1))
    points = [Point(xv.flat[i], yv.flat[i]) for i in range(xv.size)]
    nodal_coords = np.array([[pt.x, pt.y] for pt in points if poly.intersects(pt)])
    dof = np.ones((len(nodal_coords), 2))

    # Default load point
    if loaded_points is None:
        loaded_points = [[width, height // 2]]
    # support conditions
    for i, node in enumerate(nodal_coords):
        if support_points == []:
            if node[0] == 0:
                dof[i, :] = [0, 0]  # Support nodes with x=0
        else:
            dof[i, :] = (
                [0, 0]
                if any((node == point).all() for point in support_points)
                else [1, 1]
            )
    dof = np.array(dof).flatten()

    # Generate all pattern loads
    # ns-rse 2026-03-17 : Unused arguments but may combine all_patterns and patternodal_coordsescriptions to dict
    # all_patterns, base_load, patternodal_coordsescriptions = mqake_pattern_loads(
    all_patterns, _, _ = make_pattern_loads(
        nodal_coords, loaded_points, load_large, load_small, load_val
    )

    # Create the 'ground structure'
    # PML = 'potential member list'
    potential_members = []
    for i, j in itertools.combinations(range(len(nodal_coords)), 2):
        dx, dy = (
            abs(nodal_coords[i][0] - nodal_coords[j][0]),
            abs(nodal_coords[i][1] - nodal_coords[j][1]),
        )
        l = np.sqrt(dx**2 + dy**2)
        # Remove overlapping members, or members longer than maxLength
        if (l < max_length and gcd(int(dx), int(dy)) == 1) or joint_cost != 0:
            seg = [] if convex else LineString([nodal_coords[i], nodal_coords[j]])
            if convex or poly.contains(seg) or poly.boundary.contains(seg):
                potential_members.append([i, j, l, False])
    potential_members = np.array(potential_members)

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
    print(f"Setup took {setup_end - setup_start!s}")
    print(
        f"Nodes: {len(nodal_coords)} Members: {len(potential_members)} Total load patterns: {len(all_patterns)}"
    )

    vol = 1e9  # arbitrary large number to initialise
    # Start the 'member adding' loop
    for itr in range(1, 100):
        last_volume = vol
        # Get active members/parts of matrices
        c_n = potential_members[potential_members[:, 3] == True]  # pylint: disable=singleton-comparison

        # Get active pattern loads
        f_active = [
            all_patterns[k]
            for k in range(len(all_patterns))
            if active_load_cases[k] == 1
        ]

        # solve current reduced problem
        vol, a, q, u = solve(
            nodal_coords,
            c_n,
            f_active,
            dof,
            stress_tensile,
            stress_compressive,
            joint_cost,
        )

        # output
        if isinf(vol):
            print("Error: infeasible problem detected")
            return [], [], []
        n_active = int(np.sum(active_load_cases))
        print(
            f"Itr: {itr}, vol: {vol}, mems: {len(c_n)} active load cases:{n_active}/{len(all_patterns)}"
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
                    nodal_coords, c_n, q, all_patterns, active_load_cases, dof
                )
            elif primal_method == "load_factor":
                # Use load factor LP
                converged = stop_primal_violation_pattern(
                    nodal_coords,
                    c_n,
                    a,
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
    print(f"Volume: {final_vol}")
    solve_end = time.process_time()
    print("Solve took " + str(solve_end - setup_end))
    print(f"Active patterns: {int(np.sum(active_load_cases))}/{len(all_patterns)}")

    # Plot results
    # plotTruss(nodal_coords, c_n, a, q, max(a)*1e-2, "Final", update=False, allCases=True)

    ## Filter
    if filtering:
        filter_levels = [
            0.001,
            0.01,
            0.02,
            0.03,
            0.04,
            0.05,
            0.06,
            0.07,
            0.08,
            0.09,
            0.1,
        ]
    else:
        filter_levels = []
    for multiplier in filter_levels:
        max_a = max(a)
        filter_val = multiplier * max_a
        keep = [a_value > filter_val for a_value in a]
        kept = c_n[keep]
        vol, filer_a, filter_q, u = solve(
            nodal_coords,
            kept,
            f_active,
            dof,
            stress_tensile,
            stress_compressive,
            joint_cost,
        )
        if vol > 0:
            print(
                f"filtered volume {vol} with filter at {100 * multiplier}% gives {len(filer_a)!s} members"
            )
            plot_truss(
                nodal_coords=nodal_coords,
                c_n=kept,
                areas=filer_a,
                forces=filter_q,
                threshold=max(a) * 1e-3,
                title="Filtered " + str(100 * multiplier) + "%",
                update=False,
                all_cases=False,
            )

    print(f"Plotting took {time.process_time() - solve_end!s}")

    # Save results to CSV
    if save_to_csv:
        results = {
            "timestamp": timestamp,
            "problem_name": problem_name or f"w{width}_h{height}_n{len(loaded_points)}",
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
            # 'cpu_time_total': total_cpu_time,
            # 'wall_time_total': total_wall_time,
            "primal_method": primal_method,
            "notes": notes,
        }
        # ns-rse 2026-03-16 - inefficient to write to CSV, build dictionary/dataframe in memory and write to disk on
        #                     completion (as we may end up paralllelising processing)
        save_results_to_csv(results, csv_filename)

    return vol, a


def save_results_to_csv(
    results: dict[str, str | int | float], filename="pattern_loading_results.csv"
):
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
        - n_patterns_total, n_patterns_active
        - load_large, load_small
        - iterations
        - final_volume
        - n_members_final
        - n_nodes, n_ground_structure
        - cpu_time_setup, cpu_time_solve
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

    print(f"\nResults saved to {filename}")


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
