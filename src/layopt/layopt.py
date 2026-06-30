"""Layopt module."""

# -*- coding: utf-8 -*-
## This file forms supplementary material to the paper
## "Adaptive topology optimization of fail-safe truss structures" by
## Helen E. Fairclough Â· Linwei He Â· Tekle B. Asfaha Â· Sam Rigby

## This code has been developed based on the code of
## He, L., Gilbert, M. & Song, X. A Python script for adaptive layout
## optimization of trusses. Struct Multidisc Optim 60, 835â€“847 (2019).
## https://doi.org/10.1007/s00158-019-02226-6

import time
from math import ceil, isinf
from pathlib import Path

import cvxpy as cvx
import numpy as np
import numpy.typing as npt
import pandas as pd
from loguru import logger
from scipy import sparse

from layopt import structure
from layopt.classes import Parameters
from layopt.io import dict_to_df, get_date_time
from layopt.plotting import plot_truss


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
    solver: str,
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
    solver : str
        CVXPY solver name.

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
    problem.solve(solver)

    vol = 0.0 if problem.value is None else problem.value
    areas = np.zeros(n_members) if a.value is None else a.value
    forces = [np.zeros(n_members) if qi.value is None else qi.value for qi in q_vars]

    # eq_constraints = constraints[::3]  # every third constraint is the equilibrium one
    deflections = []
    for eq_con in eq_constraints:
        dual = eq_con.dual_value
        if dual is None:
            dual = np.zeros(eq_matrix_b.shape[0])
        deflections.append(-np.array(dual))

    if vol == 0:
        deflections = [ui * 10000 for ui in deflections]

    return vol, areas, forces, deflections


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
    forces: list[npt.NDArray[np.float64]],
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
    solver: str,
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
    solver : str
        CVXPY solver name.

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
        problem.solve(solver)

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
    parameters: Parameters,
) -> tuple[float, dict[int, float], pd.DataFrame] | None:
    """
    Main function, perform adaptive member adding procedure with multiple load cases.

    Parameters
    ----------
    parameters : Parameters
        Parameters class with all attributes for the modelling. If not already instantiated then you can pass
        ``parameters = Parameters(**config)`` if you have a dictionary of parameters stored in ``config``.

    Returns
    -------
    tuple[float, dict[int, float], pd.DataFrame, float]
        A tuple consisting of ``volume`` (the final volume of the solved problem) and ``member_areas_filtered``
        (dict with keys ground structure member indices and values corresponding to the final member areas of
        the solved problem), and a data frame of results.
    """
    setup_start = time.process_time()
    # Make domain
    bounding_coordinates = np.asarray(
        [
            [0, 0],
            [parameters.width, 0],
            [parameters.width, parameters.height],
            [0, parameters.height],
        ]
    )
    poly = structure.make_polygon(bounding_coordinates)
    convex = poly.convex_hull.area == poly.area
    logger.debug(f"Domain created, convex? : {convex=}")

    # Make nodes
    nodal_coords: npt.NDArray[np.float64] = structure.create_nodes(
        width=parameters.width, height=parameters.height, polygon=poly
    )
    logger.debug(f"Node coordinates :\n{nodal_coords=}")

    # Default load point
    if parameters.loaded_points is None:
        parameters.loaded_points = structure.calc_default_loaded_points(
            width=parameters.width, height=parameters.height
        )
        logger.info(
            f"Loaded points not provided, calculated as : {parameters.loaded_points=}"
        )
    # Calculate support conditions/degrees of freedom
    dof = structure.support_conditions(
        nodal_coords=nodal_coords, support_points=parameters.support_points
    )
    logger.debug(f"Degrees of Freedom : {dof=}")
    # Generate all pattern loads
    # ns-rse 2026-03-17 : Unused return arguments but may combine all_patterns and pattern_descriptions to dict
    # all_patterns, base_load, pattern_descriptions = make_pattern_loads(
    # ns-rse 2026-05-13 - loaded_points and load_direction are proposed to be attributes of CaseFamily
    all_patterns, _, _ = structure.make_pattern_loads(
        nodal_coords,
        parameters.loaded_points,
        parameters.load_large,
        parameters.load_small,
        parameters.load_direction,
    )

    # Create the 'ground structure'
    potential_members = structure.calc_potential_members(
        nodal_coords=nodal_coords,
        max_length=parameters.max_length,
        joint_cost=parameters.joint_cost,
        convex=convex,
        polygon=poly,
        active_member_threshold=parameters.active_member_threshold,
    )
    # Primal adaptivity: start with base load case only ####
    primal_adaptivity, active_load_cases = structure.primal_adaptivity(
        primal_method=parameters.primal_method, all_patterns_length=len(all_patterns)
    )

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
            parameters.stress_tensile,
            parameters.stress_compressive,
            parameters.joint_cost,
            parameters.cvxpy["solver"],
        )
        # We need to solve once so that we have valid values for `filter_areas ` which we then filter based on `fitler_level[s]`
        # (rename to `filter_level` but need to check first if that is what we want to parallelise on or if it is
        # `primal_method`).

        # output
        if isinf(vol):
            logger.error("Infeasible problem detected")
            return None
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
            parameters.stress_tensile,
            parameters.stress_compressive,
            u,
            parameters.joint_cost,
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
            if parameters.primal_method == "residual":
                # Use equilibrium residual check
                converged = stop_primal_violation_residual(
                    nodal_coords,
                    c_n,
                    filter_forces,
                    all_patterns,
                    active_load_cases,
                    dof,
                )
            elif parameters.primal_method == "load_factor":
                # Use load factor LP
                converged = stop_primal_violation_pattern(
                    nodal_coords,
                    c_n,
                    filter_areas,
                    all_patterns,
                    active_load_cases,
                    dof,
                    parameters.stress_tensile,
                    parameters.stress_compressive,
                    parameters.cvxpy["solver"],
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
    results = {}
    for filter_level in parameters.filter_levels:
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
                parameters.stress_tensile,
                parameters.stress_compressive,
                parameters.joint_cost,
                parameters.cvxpy["solver"],
            )
            logger.info(f"Volume (filter_level = {filter_level}): {final_vol}")
        # Build dictionary of results (the final_vol changes if we have filtered above)
        results[filter_level] = {
            "timestamp": get_date_time(),
            "problem_name": parameters.problem_name
            or f"w{parameters.width}_h{parameters.height}_n{len(parameters.loaded_points)}",
            "filter_level": filter_level,
            "width": parameters.width,
            "height": parameters.height,
            "n_load_points": len(parameters.loaded_points),
            "n_patterns_total": len(all_patterns),
            "n_patterns_active": int(np.sum(active_load_cases)),
            "load_large": parameters.load_large,
            "load_small": parameters.load_small,
            "iterations": itr,
            "final_volume": final_vol,
            "n_members_final": len(c_n),
            "n_nodes": len(nodal_coords),
            "n_ground_structure": len(potential_members),
            "cpu_time_setup": setup_end - setup_start,
            "cpu_time_solve": solve_end - setup_end,
            "primal_method": parameters.primal_method,
            "notes": parameters.notes,
        }

        # Plot results
        if parameters.plotting["run"]:
            outfile = Path(parameters.output_dir) / (
                parameters.problem_name.replace(" ", "_")
                + f"_w{parameters.width}_h{parameters.height}_n{len(parameters.loaded_points)}_filter{int(filter_level * 100)}"
            )
            if vol > 0:
                _, _ = plot_truss(
                    nodal_coords=nodal_coords,
                    c_n=c_n,
                    areas=filter_areas,
                    forces=filter_forces,
                    threshold=max(filter_areas) * parameters.member_area_filtering,
                    title="Filtered " + str(100 * filter_level) + "%",
                    bar_thickness=parameters.plotting["bar_thickness"],
                    dpi=parameters.plotting["dpi"],
                    outfile=outfile,
                )
            else:
                logger.warning("No plot generated as volume <= 0.0")
        logger.info(f"Plotting took {time.process_time() - solve_end!s}")

    member_areas_filtered = member_area_filtering(
        active_indices=np.where(potential_members[:, 3])[0],
        filter_areas=filter_areas,
        filtering_threshold=parameters.member_area_filtering,
    )
    logger.info(
        f"Area filtering at {parameters.member_area_filtering} ({100 * parameters.member_area_filtering}% of max): "
        f"{len(member_areas_filtered)} members retained"
    )
    return (vol, member_areas_filtered, dict_to_df(results))


def member_area_filtering(
    active_indices: npt.NDArray[np.float64],
    filter_areas: npt.NDArray[np.float64],
    filtering_threshold: float,
) -> dict[int, float]:
    """
    Filter output members by area threshold.

    Build a dictionary of areas where keys are ground structure member indices, filtering potential members for those
    that exceed the threshold.

    Parameters
    ----------
    active_indices : npt.NDArray[np.int]
        Active indices to filter.
    filter_areas : npt.NDArray[np.float64]
        Areas to be filtered.
    filtering_threshold : float
        Filtering threshold.

    Returns
    -------
    dict[int, float]
        Dictionary of areas that exceed the threshold.
    """
    keep = filter_areas >= (max(filter_areas) * filtering_threshold)
    return {
        int(idx): float(area)
        for idx, area in zip(active_indices[keep], filter_areas[keep], strict=True)
    }
