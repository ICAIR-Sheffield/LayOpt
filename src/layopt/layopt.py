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
import os
import time
from math import ceil, gcd, isinf

import matplotlib.pyplot as plt
import mosek.fusion as mosek
import numpy as np
from scipy import sparse

# from numpy.matlib import repmat
from shapely.geometry import LineString, Point, Polygon

plt.rcParams["figure.max_open_warning"] = 0


# Calculate equilibrium matrix B
def calcB(Nd, Cn, dof):
    m, n1, n2 = len(Cn), Cn[:, 0].astype(int), Cn[:, 1].astype(int)
    l, X, Y = Cn[:, 2], Nd[n2, 0] - Nd[n1, 0], Nd[n2, 1] - Nd[n1, 1]
    d0, d1, d2, d3 = dof[n1 * 2], dof[n1 * 2 + 1], dof[n2 * 2], dof[n2 * 2 + 1]
    s = np.concatenate((-X / l * d0, -Y / l * d1, X / l * d2, Y / l * d3))
    r = np.concatenate((n1 * 2, n1 * 2 + 1, n2 * 2, n2 * 2 + 1))
    c = np.concatenate((np.arange(m), np.arange(m), np.arange(m), np.arange(m)))
    return sparse.coo_matrix((s, (r, c)), shape=(len(Nd) * 2, m))


# Solve linear programming problem with given connections and pattern load cases
def solveLP(Nd, Cn, f, dof, st, sc, jc):
    l = [col[2] + jc for col in Cn]
    B = calcB(Nd, Cn, dof)
    q, eqn = [], []
    k = 0  # (damage+load) case number
    with mosek.Model() as M:
        a = M.variable("a", len(Cn), mosek.Domain.greaterThan(0.0))
        B = mosek.Matrix.sparse(B.shape[0], B.shape[1], B.row, B.col, B.data)
        M.objective(mosek.ObjectiveSense.Minimize, mosek.Expr.dot(l, a))
        for fk in f:
            qi = M.variable(len(Cn))
            q.append(qi)
            eqni = M.constraint(
                mosek.Expr.sub(mosek.Expr.mul(B, q[k]), fk * dof),
                mosek.Domain.equalsTo(0),
            )
            eqn.append(eqni)
            M.constraint(
                mosek.Expr.sub(mosek.Expr.mul(sc, a), q[k]), mosek.Domain.greaterThan(0)
            )
            M.constraint(
                mosek.Expr.sub(mosek.Expr.mul(-st, a), q[k]), mosek.Domain.lessThan(0)
            )
            k += 1
        M.setSolverParam("optimizer", "intpnt")
        M.setSolverParam("intpntBasis", "never")
        M.acceptedSolutionStatus(mosek.AccSolutionStatus.Anything)
        # M.setLogHandler(stdout)
        M.solve()
        vol = M.primalObjValue()
        q = [np.array(qi.level()) for qi in q]
        a = a.level()
        u = [-np.array(eqnk.dual()) for eqnk in eqn]
        if vol == 0:
            u = [ui * 10000 for ui in u]

    return vol, a, q, u


# Add new members dual violation
def stopViolation(Nd, PML, dof, st, sc, u, jc):
    lst = np.where(PML[:, 3] == False)[0]
    Cn = PML[lst]
    l = Cn[:, 2] + jc
    B = calcB(Nd, Cn, dof).tocsc()
    y = np.zeros(len(Cn))
    for k, uk in enumerate(u):
        yk = np.multiply(B.transpose().dot(uk) / l, np.array([[st], [-sc]]))
        y += np.amax(yk, axis=0)
    vioCn = np.where(y > 1.000)[0]
    vioSort = np.flipud(np.argsort(y[vioCn]))
    num = ceil(0.1 * (len(PML) - len(Cn)))  # size of existing problem
    for i in range(min(num, len(vioSort))):
        PML[lst[vioCn[vioSort[i]]]][3] = True  # set member as active
    return min(num, len(vioSort))


# Visualize truss
def plotTruss(Nd, Cn, a, q, threshold, st, update=True, allCases=False):
    if allCases == True:
        plotAllCases(Nd, Cn, a, q, threshold, st)
    else:
        fig = plt.figure()
        ax = fig.subplots()
        plt.ion() if update else plt.ioff()
        ax.axis("off")
        ax.axis("equal")
        ax.set_title(st)
        tk = 0.4  # bar thickness scale
        for i in [i for i in range(len(a)) if a[i] >= threshold]:
            if len(q) > 1:  # multiple LC coloring
                if all([q[lc][i] >= -0.001 for lc in range(len(q))]):
                    c = "r"
                elif all([q[lc][i] <= 0.001 for lc in range(len(q))]):
                    c = "b"
                else:
                    c = "tab:gray"
            else:  # single LC coloring (black = no load, dark = less load)
                c = (min(max(q[0][i] / a[i], 0), 1), 0, min(max(-q[0][i] / a[i], 0), 1))
            pos = Nd[Cn[i, [0, 1]].astype(int), :]
            ax.plot(
                pos[:, 0],
                pos[:, 1],
                color=c,
                linewidth=a[i] * tk,
                solid_capstyle="round",
            )
        plt.pause(0.01) if update else plt.show()
        # fig.savefig(st+'.pdf', dpi=1200)


# loop through all cases and plot individually
def plotAllCases(Nd, Cn, a, q, threshold, st):
    numCases = len(q)
    for k in range(numCases):
        plotTruss(
            Nd,
            Cn,
            a,
            [q[k]],
            threshold,
            st + " case " + str(k),
            update=True,
            allCases=False,
        )


# generate all 2^n combinations of large/small loads at each load point
def makePatternLoads(Nd, loadedPoints, loadLarge=50, loadSmall=5, loadDir=[0, -1]):
    n = len(loadedPoints)

    # Find node indices for each load point
    loadNodeIndices = []
    for ldPt in loadedPoints:
        dists = np.linalg.norm(Nd - np.array(ldPt), axis=1)
        loadNodeIndices.append(np.argmin(dists))

    allPatterns = []
    patternDescriptions = []

    # Generate all 2^n combinations
    # First combo (all loadLarge) is base case
    for combo in itertools.product([loadLarge, loadSmall], repeat=n):
        fk = np.zeros(len(Nd) * 2)
        desc = []
        for pt_idx, magnitude in enumerate(combo):
            node = loadNodeIndices[pt_idx]
            fk[node * 2] += magnitude * loadDir[0]
            fk[node * 2 + 1] += magnitude * loadDir[1]
            desc.append(f"pt{pt_idx}={'L' if magnitude == loadLarge else 'S'}")

        allPatterns.append(fk)
        patternDescriptions.append(", ".join(desc))

    baseLoad = allPatterns[0]  # First pattern = all large loads

    print(f"\nPattern loading: {n} load points -> {len(allPatterns)} total patterns")
    print(f"Base case (all large): {patternDescriptions[0]}")

    return allPatterns, baseLoad, patternDescriptions


# add new pattern load cases primal violation
# violation criterion: check if min over active j of ||B*q[j] - f[k]*dof|| > tol
# (essentially checking if Bq-f=0)
# for each inactive load pattern, check whether any existing active solution
# q[j] already satisfies equilibrium for that load pattern. if not, pattern
# is violated and is added
def stopPrimalViolationResidual(Nd, Cn, q, allPatterns, activeLoadCases, dof):
    tol = 1e-5
    B = calcB(Nd, Cn, dof).tocsc()

    totalViolation = np.zeros(len(allPatterns))

    # loop through all (active and inactive) pattern load cases
    for k in range(len(allPatterns)):
        if activeLoadCases[k] == 1:
            continue  # skip active cases

        fk_dof = allPatterns[k] * dof
        residuals = []
        for qj in q:
            # store ||B*q[j] - f[k]*dof||
            residual = np.linalg.norm(B.dot(qj) - fk_dof)
            residuals.append(residual)

        # find min of residuals over active pattern load cases
        totalViolation[k] = min(residuals)

    violated = totalViolation > tol  # true if there are violated cases need to be added
    numToAdd = max(1, ceil(len(allPatterns) / 10))  # limit on num to add

    if any(violated):
        # Sort by violation severity
        byViolation = sorted(
            [i for i in range(len(totalViolation)) if totalViolation[i] > tol],
            key=lambda k: totalViolation[k],
            reverse=True,
        )

        if len(byViolation) == 0:
            return True

        # Active most violated load pattern
        activeLoadCases[byViolation[0]] = 1
        addedThisIter = [byViolation[0]]
        byViolation.pop(0)

        # Add distinct cases
        # distinct if violated load pattern vector (after normalisation)
        # is not parallel to added load pattern vector (after normalisation)
        # (with current loading everything should be distinct?)
        for _ in range(numToAdd - 1):
            if len(byViolation) == 0:
                break
            addedACase = False
            for k in byViolation:
                fk = allPatterns[k]
                fk_norm = fk / (np.linalg.norm(fk) + 1e-12)
                isDistinct = True
                for j in addedThisIter:
                    fj = allPatterns[j]
                    fj_norm = fj / (np.linalg.norm(fj) + 1e-12)
                    if np.dot(fk_norm, fj_norm) > 0.99:
                        isDistinct = False
                        break
                if isDistinct:
                    activeLoadCases[k] = 1
                    addedThisIter.append(k)
                    byViolation.remove(k)
                    addedACase = True
                    break
            if not addedACase:
                break

        return False  # cases added, keep going
    return True  # converged, terminate


# add new pattern load cases primal violation using load factor structural analysis
# for each inactive load pattern f[k], solve an LP to find the maximum
# load factor lambda that the current design (with fixed member areas a) can carry:
#    maximize lambda
#    subject to:
#        B*q = lambda*f[k]        (equilibrium with scaled load)
#        -sigma_c*a <= q <= sigma_t*a  (stress limits with fixed areas)
# violation criterion: check if lambda >= 1
# if so, structure can carry full load so no violation
# else structure can only carry some of the load, violation, so add load case
def stopPrimalViolationPattern(Nd, Cn, a, allPatterns, activeLoadCases, dof, st, sc):
    tol = 0.99  # lambda must be >= 1 to be considered feasible

    B = calcB(Nd, Cn, dof)
    loadFactors = np.ones(len(allPatterns))  # lambda=1 for active cases

    # loop through all (active and inactive) pattern load cases
    for k in range(len(allPatterns)):
        if activeLoadCases[k] == 1:
            continue  # skip active cases

        fk_dof = allPatterns[k] * dof

        # Solve LP: maximize lambda subject to B*q = lambda*f, -sigma*a <= q <= sigma*a
        with mosek.Model() as M:
            # Variables
            q_var = M.variable("q", len(Cn))
            lambda_var = M.variable("lambda", 1, mosek.Domain.greaterThan(0.0))

            # Objective: maximize lambda
            M.objective(mosek.ObjectiveSense.Maximize, lambda_var)

            # Constraint 1: B*q = lambda*f
            B_mosek = mosek.Matrix.sparse(B.shape[0], B.shape[1], B.row, B.col, B.data)
            M.constraint(
                mosek.Expr.sub(
                    mosek.Expr.mul(B_mosek, q_var),
                    mosek.Expr.mul(fk_dof, lambda_var.index(0)),
                ),
                mosek.Domain.equalsTo(0),
            )

            # Constraint 2: q <= sigma_t * a (tension limit)
            M.constraint(mosek.Expr.sub(q_var, st * a), mosek.Domain.lessThan(0))

            # Constraint 3: q >= -sigma_c * a (compression limit)
            M.constraint(mosek.Expr.sub(q_var, -sc * a), mosek.Domain.greaterThan(0))

            # Solve
            M.setSolverParam("optimizer", "intpnt")
            M.acceptedSolutionStatus(mosek.AccSolutionStatus.Anything)
            M.solve()
            loadFactors[k] = lambda_var.level()[0]

    # Violation: load factor < 1 (with tolerance)
    violated = loadFactors < tol
    numToAdd = max(1, ceil(len(allPatterns) / 10))

    if any(violated):
        # Sort by severity: lowest load factor = most violated
        byViolation = sorted(
            [i for i in range(len(loadFactors)) if violated[i]],
            key=lambda k: loadFactors[k],
        )

        if len(byViolation) == 0:
            return True

        # Add most violated (lowest lambda)
        most_violated_id = byViolation[0]
        activeLoadCases[most_violated_id] = 1
        print(
            f"  Adding most violated pattern {byViolation[0]}: lambda={loadFactors[most_violated_id]:.3f}"
        )
        addedThisIter = [byViolation[0]]
        byViolation.pop(0)

        # Add distinct cases
        # distinct if load factor is +/-10% of added load factor
        # and if violated load pattern vector (after normalisation)
        # is not parallel to added load pattern vector (after normalisation)
        # (with current loading no load pattern vectors should be parallel?)
        for _ in range(numToAdd - 1):
            if len(byViolation) == 0:
                break
            addedACase = False
            for k in byViolation:
                # check if load case k has a significantly different load factor
                # from all load cases added this iteration
                isDistinct = True
                for j in addedThisIter:
                    # check if both load factors are approx 0, only add one if so
                    if loadFactors[k] < 0.01 and loadFactors[j] < 0.01:
                        isDistinct = False
                        break
                    # if added load factor is 0 but other violated ones aren't,
                    # other violated cases are distinct
                    if loadFactors[j] < 0.01:
                        continue
                    # check ratio of load factors if neither approx 0
                    lambda_ratio = loadFactors[k] / (loadFactors[j] + 1e-12)
                    if 0.9 < lambda_ratio < 1.1:  # Within 10% of each other
                        isDistinct = False
                        break
                if isDistinct:
                    fk = allPatterns[k]
                    fk_norm = fk / (np.linalg.norm(fk) + 1e-12)
                    isDistinct = True
                    for j in addedThisIter:
                        fj = allPatterns[j]
                        fj_norm = fj / (np.linalg.norm(fj) + 1e-12)
                        if np.dot(fk_norm, fj_norm) > 0.99:
                            isDistinct = False
                            break
                if isDistinct:
                    activeLoadCases[k] = 1
                    print(
                        f"  Adding {len(addedThisIter) + 1} distinct pattern {k}: lambda={loadFactors[k]:.3f}"
                    )
                    addedThisIter.append(k)
                    byViolation.remove(k)
                    addedACase = True
                    break
            if not addedACase:
                break

        return False  # cases added, keep going
    return True  # converged, terminate


# Main function - edited for pattern loading
def trussopt(
    width,
    height,
    st=1,
    sc=1,
    jc=0,
    loadedPoints=[],
    loadVal=[0, -1],
    loadLarge=50,
    loadSmall=5,
    maxLength=1000,
    supportPoints=[],
    doFilter=False,
    primal_method="load_factor",
    problem_name="",
    save_to_csv=True,
    csv_filename="pattern_loading_results.csv",
    notes="",
):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    setupStart = time.process_time()

    # Make domain
    poly = Polygon([(0, 0), (width, 0), (width, height), (0, height)])
    convex = True if poly.convex_hull.area == poly.area else False

    # Make nodes
    xv, yv = np.meshgrid(range(width + 1), range(height + 1))
    pts = [Point(xv.flat[i], yv.flat[i]) for i in range(xv.size)]
    Nd = np.array([[pt.x, pt.y] for pt in pts if poly.intersects(pt)])
    dof = np.ones((len(Nd), 2))

    # Default load point
    if loadedPoints == []:
        loadedPoints = [[width, height // 2]]
    # support conditions
    for i, nd in enumerate(Nd):
        if supportPoints == []:
            if nd[0] == 0:
                dof[i, :] = [0, 0]  # Support nodes with x=0
        else:
            dof[i, :] = (
                [0, 0]
                if any([(nd == supPt).all() for supPt in supportPoints])
                else [1, 1]
            )
    dof = np.array(dof).flatten()

    # Generate all pattern loads
    allPatterns, baseLoad, patternDescriptions = makePatternLoads(
        Nd, loadedPoints, loadLarge, loadSmall, loadVal
    )

    # Create the 'ground structure'
    # PML = 'potential member list'
    PML = []
    for i, j in itertools.combinations(range(len(Nd)), 2):
        dx, dy = abs(Nd[i][0] - Nd[j][0]), abs(Nd[i][1] - Nd[j][1])
        l = np.sqrt(dx**2 + dy**2)
        # Remove overlapping members, or members longer than maxLength
        if (l < maxLength and gcd(int(dx), int(dy)) == 1) or jc != 0:
            seg = [] if convex else LineString([Nd[i], Nd[j]])
            if convex or poly.contains(seg) or poly.boundary.contains(seg):
                PML.append([i, j, l, False])
    PML = np.array(PML)

    # Create the active members
    DualAdaptivity = True
    startLen = 1.5 if DualAdaptivity else 10000
    for pm in [p for p in PML if p[2] <= startLen]:  # Activate short members (adaptive)
        pm[3] = True

    #### Primal adaptivity: start with base load case only ####
    PrimalAdaptivity = True
    # if PrimalAdaptivity:
    #     activeLoadCases = np.zeros(len(allPatterns), dtype=int)
    #     activeLoadCases[0] = 1  # Base case = all large loads
    # # does below make sense here?
    # else:
    #     activeLoadCases = np.ones(len(allPatterns), dtype=int)
    if primal_method == "residual" or primal_method == "load_factor":
        PrimalAdaptivity = True
        activeLoadCases = np.zeros(len(allPatterns), dtype=int)
        activeLoadCases[0] = 1  # Base case = all large loads
    else:
        PrimalAdaptivity = False
        activeLoadCases = np.ones(len(allPatterns), dtype=int)

    setupEnd = time.process_time()
    print("Setup took " + str(setupEnd - setupStart))
    print(
        "Nodes: %d Members: %d Total load patterns: %d"
        % (len(Nd), len(PML), len(allPatterns))
    )

    vol = 1e9  # arbitrary large number to initialise
    # Start the 'member adding' loop
    for itr in range(1, 100):
        lastVol = vol
        # Get active members/parts of matrices
        Cn = PML[PML[:, 3] == True]

        # Get active pattern loads
        f_active = [
            allPatterns[k] for k in range(len(allPatterns)) if activeLoadCases[k] == 1
        ]

        # solve current reduced problem
        vol, a, q, u = solveLP(Nd, Cn, f_active, dof, st, sc, jc)

        # output
        if isinf(vol):
            print("Error: infeasible problem detected")
            return [], [], []
        nActive = int(np.sum(activeLoadCases))
        print(
            "Itr: %d, vol: %f, mems: %d active load cases:%d/%d"
            % (itr, vol, len(Cn), nActive, len(allPatterns))
        )
        # plot interim solutions (slow)
        # plotTruss(Nd, Cn, a, q, max(a) * 1e-2, "Itr:" + str(itr), extraPlot = activeDamageDef)

        # inner loop - adding of members based on dual violation
        # still need PMLcache? currently unused
        # PMLcache = np.copy(PML[:,3])
        numAdded = stopViolation(Nd, PML, dof, st, sc, u, jc)
        if not (vol > 0.99 * lastVol and vol < 1.0001 * lastVol):
            continue  # small vol decrease = member adding close to convergence

        # outer loop - adding of pattern load cases based on primal violation
        # if stopPrimalViolationPattern(Nd, Cn, a, allPatterns, activeLoadCases, dof, st, sc):
        #     if numAdded > 0: # only fully terminate when no members violate
        #         continue
        #     else:
        #         break

        if PrimalAdaptivity:
            if primal_method == "residual":
                # Use equilibrium residual check
                converged = stopPrimalViolationResidual(
                    Nd, Cn, q, allPatterns, activeLoadCases, dof
                )
            elif primal_method == "load_factor":
                # Use load factor LP
                converged = stopPrimalViolationPattern(
                    Nd, Cn, a, allPatterns, activeLoadCases, dof, st, sc
                )

            if not converged:
                continue  # Cases added, keep iterating
            if numAdded > 0:
                continue  # No cases added but members added
            break  # Both converged
        # No primal adaptivity - just check member convergence
        if numAdded == 0:
            break  # Converged

    final_vol = vol
    print("Volume: %f" % (final_vol))
    solveEnd = time.process_time()
    print("Solve took " + str(solveEnd - setupEnd))
    print(f"Active patterns: {int(np.sum(activeLoadCases))}/{len(allPatterns)}")

    # Plot results
    # plotTruss(Nd, Cn, a, q, max(a)*1e-2, "Final", update=False, allCases=True)

    ## Filter
    if doFilter:
        FilterLevels = [
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
        FilterLevels = []
    for multiplier in FilterLevels:
        maxA = max(a)
        filterVal = multiplier * maxA
        keep = [True if aVal > filterVal else False for aVal in a]
        kept = Cn[keep]
        vol, FiltA, FiltQ, u = solveLP(Nd, kept, f_active, dof, st, sc, jc)
        if vol > 0:
            print(
                "filtered volume ",
                vol,
                "with filter at",
                100 * multiplier,
                "% gives",
                str(len(FiltA)),
                "members",
            )
            plotTruss(
                Nd,
                kept,
                FiltA,
                FiltQ,
                max(a) * 1e-3,
                "Filtered " + str(100 * multiplier) + "%",
                False,
                allCases=False,
            )

    print("Plotting took " + str(time.process_time() - solveEnd))

    # Save results to CSV
    if save_to_csv:
        results = {
            "timestamp": timestamp,
            "problem_name": problem_name or f"w{width}_h{height}_n{len(loadedPoints)}",
            "width": width,
            "height": height,
            "n_load_points": len(loadedPoints),
            "n_patterns_total": len(allPatterns),
            "n_patterns_active": int(np.sum(activeLoadCases)),
            "load_large": loadLarge,
            "load_small": loadSmall,
            "iterations": itr,
            "final_volume": final_vol,
            "n_members_final": len(Cn),
            "n_nodes": len(Nd),
            "n_ground_structure": len(PML),
            "cpu_time_setup": setupEnd - setupStart,
            "cpu_time_solve": solveEnd - setupEnd,
            # 'cpu_time_total': total_cpu_time,
            # 'wall_time_total': total_wall_time,
            "primal_method": primal_method,
            "notes": notes,
        }
        save_results_to_csv(results, csv_filename)

    return vol, a


def save_results_to_csv(results, filename="pattern_loading_results.csv"):
    """
    Save optimization results to CSV file.

    Creates file with header if it doesn't exist, otherwise appends.

    Parameters:
    -----------
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
        CSV filename (default: 'pattern_loading_results.csv')
    """
    file_exists = os.path.isfile(filename)

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

    with open(filename, "a", newline="") as csvfile:
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

# =============================================================================
# ==== Short cantilever (Fig 9 etc., edited for pattern loading) ==============
# =============================================================================
# L = 3
# trussopt(width=L, height=2*L,
#          loadedPoints=[[L, L]],  # 1 load point, 2 patterns
#          loadLarge=50, loadSmall=5,
#          loadVal=[0, -1],
#          maxLength=6*L)
# print("Normalised Volume = ", v/L, "FL")

# =============================================================================
# ==== Square cantilever (Fig 12b etc., edited for pattern loading) ===========
# =============================================================================
# trussopt(width=8, height=8,
#          loadedPoints=[[8, 0], [8, 4]],  # 2 load points, 4 patterns
#          loadLarge=50, loadSmall=5,
#          loadVal=[0, -1],
#          maxLength=15)

# =============================================================================
# ==== Parallel forces (Table 2, edited for pattern loading) ==================
# =============================================================================
# trussopt(width=3, height=1,
#          loadedPoints=[[3, 0], [3, 1]],  # 2 load points, 4 patterns
#          loadLarge=50, loadSmall=5,
#          loadVal=[1, 0],  # horizontal loading
#          maxLength=2.5)

# =============================================================================
# ==== Spanning Example (Fig 16 etc.) =========================================
# =============================================================================
height = 4
spanL = 18
numSpans = 1
totalW = spanL * numSpans
numPerSpan = 9  # Nodes per span

loadPoints = [
    [x * spanL / numPerSpan, height] for x in range(numPerSpan * numSpans + 1)
]
suppPoints = [[x * spanL, 0] for x in range(numSpans + 1)]


# NB supports for arch examples hard-coded in trussopt to be fixed rather than rollers
# consider change to some sort of parameter
# trussopt(
#     width=totalW,
#     height=height,
#     loadedPoints=loadPoints,
#     loadLarge=3.75,
#     loadSmall=0.204,
#     loadVal=[0, -1],
#     supportPoints=suppPoints,
#     maxLength=2 * totalW,
#     doFilter=True,
#     primal_method="load_factor",
#     problem_name="arch_full_opt",
#     save_to_csv=True,
#     csv_filename="pattern_loading_results.csv",
#     notes="testing",
# )

# trussopt(
#     width=totalW,
#     height=height,
#     loadedPoints=loadPoints,
#     loadLarge=3.75,
#     loadSmall=0.204,
#     loadVal=[0, -1],
#     supportPoints=suppPoints,
#     maxLength=2 * totalW,
#     doFilter=True,
#     primal_method="residual",
#     problem_name="arch_residual_primal",
#     save_to_csv=True,
#     csv_filename="pattern_loading_results.csv",
#     notes="testing",
# )

# trussopt(
#     width=totalW,
#     height=height,
#     loadedPoints=loadPoints,
#     loadLarge=3.75,
#     loadSmall=0.204,
#     loadVal=[0, -1],
#     supportPoints=suppPoints,
#     maxLength=2 * totalW,
#     doFilter=True,
#     primal_method="none",
#     problem_name="arch_span_dual_only",
#     save_to_csv=True,
#     csv_filename="pattern_loading_results.csv",
#     notes="testing",
# )

# trussopt(width=totalW, height=height,
#           loadedPoints=loadPoints,
#           loadLarge=3.75, loadSmall=0.204,
#           loadVal=[0, -1],
#           supportPoints=suppPoints,
#           maxLength=2*totalW,
#           doFilter=True,
#           primal_method = 'load_factor', problem_name="three_span_full_opt",
#           save_to_csv=True, csv_filename='pattern_loading_results.csv',
#           notes="testing")

# trussopt(width=totalW, height=height,
#           loadedPoints=loadPoints,
#           loadLarge=3.75, loadSmall=0.204,
#           loadVal=[0, -1],
#           supportPoints=suppPoints,
#           maxLength=2*totalW,
#           doFilter=True,
#           primal_method = 'residual', problem_name="three_span_residual_primal",
#           save_to_csv=True, csv_filename='pattern_loading_results.csv',
#           notes="testing")

# trussopt(width=totalW, height=height,
#           loadedPoints=loadPoints,
#           loadLarge=3.75, loadSmall=0.204,
#           loadVal=[0, -1],
#           supportPoints=suppPoints,
#           maxLength=2*totalW,
#           doFilter=True,
#           primal_method = 'none', problem_name="three_span_dual_only",
#           save_to_csv=True, csv_filename='pattern_loading_results.csv',
#           notes="testing")
