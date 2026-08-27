import numpy as np

from layopt.layopt import trussopt
from layopt.classes import Parameters
from tests.conftest import trussopt_param_eighteen_by_four_spanning

resolution = 4

parameters = Parameters()
parameters.plotting["run"] = True
#parameters.max_length_initial_ground_structure = 5*resolution
parameters.width = 3*resolution
parameters.height = 2*resolution
parameters.loaded_points = np.asarray([[1*resolution,0],[2*resolution,0]])
parameters.support_points = np.asarray([[0,0],[3*resolution,0]])
parameters.problem_name = "Helen"
parameters.output_dir = "."
parameters.avg_deflection_limit = 10

testParam = Parameters(
        filter_levels=[1.0],
        width=18,
        height=4,
        stress_tensile=1,
        stress_compressive=1,
        joint_cost=0,
        loaded_points=np.asarray(
            [
                [2.0, 0],
                [4.0, 0],
                [6.0, 0],
                [8.0, 0],
                [10.0, 0],
                [12.0, 0],
                [14.0, 0],
                [16.0, 0],
            ]
        ),
        load_direction=(0, -1),
        load_large=3.75,
        load_small=0.204,
        max_length=36,
        support_points=np.asarray([[0, 0], [18, 0]]),
        primal_method="load_factor",
        problem_name="spanningexample",
        notes="spanning example test",
    )
testParam.plotting["run"] = True
testParam.output_dir = "."

testParam.avg_deflection_limit = 10
testParam.problem_name = "spanningexample_elastic"

results = trussopt(testParam)

