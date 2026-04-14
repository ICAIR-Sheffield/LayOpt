from layopt.layopt import trussopt

# =============================================================================
# ==== Short cantilever (Fig 9 etc., edited for pattern loading) ==============
# =============================================================================
L = 3
trussopt(
    width=L,
    height=2 * L,
    loaded_points=[[L, L]],  # 1 load point, 2 patterns
    load_large=50,
    load_small=5,
    load_direction=(0.0, -1.0),
    max_length=6 * L,
    support_points=[],
)
# print("Normalised Volume = ", v / L, "FL")

# =============================================================================
# ==== Square cantilever (Fig 12b etc., edited for pattern loading) ===========
# =============================================================================
trussopt(
    width=8,
    height=8,
    loaded_points=[[8, 0], [8, 4]],  # 2 load points, 4 patterns
    load_large=50,
    load_small=5,
    load_direction=[0, -1],
    max_length=15,
    support_points=[],
)

# =============================================================================
# ==== Parallel forces (Table 2, edited for pattern loading) ==================
# =============================================================================
# trussopt(width=3, height=1,
#          loaded_points=[[3, 0], [3, 1]],  # 2 load points, 4 patterns
#          load_large=50,
#          load_small=5,
#          load_direction=[1, 0],  # horizontal loading
#          max_length=2.5)

# =============================================================================
# ==== Spanning Example (Fig 16 etc.) =========================================
# =============================================================================
# height = 4
# spanL = 18
# numSpans = 1
# totalW = spanL * numSpans
# numPerSpan = 9  # Nodes per span

# loadPoints = [
#     [x * spanL / numPerSpan, height] for x in range(numPerSpan * numSpans + 1)
# ]
# suppPoints = [[x * spanL, 0] for x in range(numSpans + 1)]


# NB supports for arch examples hard-coded in trussopt to be fixed rather than rollers
# consider change to some sort of parameter
# trussopt(
#     width=totalW,
#     height=height,
#     loaded_points=loadPoints,
#     load_large=3.75,
#     load_small=0.204,
#     load_direction=[0, -1],
#     supportPoints=suppPoints,
#     max_length=2 * totalW,
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
#     loaded_points=loadPoints,
#     load_large=3.75,
#     load_small=0.204,
#     load_direction=[0, -1],
#     supportPoints=suppPoints,
#     max_length=2 * totalW,
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
#     loaded_points=loadPoints,
#     load_large=3.75,
#     load_small=0.204,
#     load_direction=[0, -1],
#     supportPoints=suppPoints,
#     max_length=2 * totalW,
#     doFilter=True,
#     primal_method="none",
#     problem_name="arch_span_dual_only",
#     save_to_csv=True,
#     csv_filename="pattern_loading_results.csv",
#     notes="testing",
# )

# trussopt(width=totalW, height=height,
#           loaded_points=loadPoints,
#           load_large=3.75, load_small=0.204,
#           load_direction=[0, -1],
#           supportPoints=suppPoints,
#           max_length=2*totalW,
#           doFilter=True,
#           primal_method = 'load_factor', problem_name="three_span_full_opt",
#           save_to_csv=True, csv_filename='pattern_loading_results.csv',
#           notes="testing")

# trussopt(width=totalW, height=height,
#           loaded_points=loadPoints,
#           load_large=3.75, load_small=0.204,
#           load_direction=[0, -1],
#           supportPoints=suppPoints,
#           max_length=2*totalW,
#           doFilter=True,
#           primal_method = 'residual', problem_name="three_span_residual_primal",
#           save_to_csv=True, csv_filename='pattern_loading_results.csv',
#           notes="testing")

# trussopt(width=totalW, height=height,
#           loaded_points=loadPoints,
#           load_large=3.75, load_small=0.204,
#           load_direction=[0, -1],
#           supportPoints=suppPoints,
#           max_length=2*totalW,
#           doFilter=True,
#           primal_method = 'none', problem_name="three_span_dual_only",
#           save_to_csv=True, csv_filename='pattern_loading_results.csv',
#           notes="testing")
