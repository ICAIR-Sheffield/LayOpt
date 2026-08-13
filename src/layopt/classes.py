"""Dataclass definitions."""

from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt
from loguru import logger
from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass
from shapely.geometry import Polygon

from layopt import structure


@dataclass(
    repr=True,
    eq=True,
    config=ConfigDict(arbitrary_types_allowed=True, validate_assignment=True),
    validate_on_init=True,
)
class Parameters:
    """Modelling parameters."""

    base_dir: Path = Field(default=Path("./"), title="Base directory")
    output_dir: str | Path = Field(
        default=Path("./output/"),
        title="Path to save the output to, default is './output/'.",
    )
    log_level: str = Field(default="info", title="Log level")
    cores: int = Field(default=2, title="Cores to run optimisation on in parallel.")
    width: int = Field(default=3, title="Width of structure.", ge=1)
    height: int = Field(default=3, title="Height of structure.", ge=1)
    steps: float = Field(default=1.0, title="Steps to generate nodes", gt=0.0)
    stress_tensile: float = Field(default=1.0, title="Tensile stress.", ge=0.0)
    stress_compressive: float = Field(default=1.0, title="Compressive stress.", ge=0.0)
    joint_cost: float = Field(default=0.0, title="Joint cost.", ge=0.0)
    loaded_points: npt.NDArray[np.int64] = Field(
        default=np.asarray([[1, 0], [2, 0]]), title="Loaded Points."
    )
    load_direction: tuple[float, float] = Field(
        default=(0.0, -1.0), title="Loaded direction."
    )
    load_large: float = Field(default=50.0, title="Maximum length.", ge=0.0)
    load_small: float = Field(default=5.0, title="Maximum length.", ge=0.0)
    max_length: float = Field(default=18.0, title="Maximum length.", ge=0.0)
    max_length_initial_ground_structure: float = Field(
        default=1.5,
        title="Threshold for marking a potential member as active in the initial ground structure.",
        gt=0.0,
    )
    support_points: npt.NDArray[np.float64] = Field(
        default=np.asarray([[0, 0, 1, 1], [3, 3, 1, 1]]),
        title="Support Points as coordinates and bools indicating whether to restrain in x- or y-directions.",
    )
    member_area_filtering: float = Field(
        default=0.001, title="Member Area Filtering", ge=0.0
    )
    cvxpy: dict[str, Any] = Field(
        default={"solver": "clarabel"},
        title="CVXPY options.",
    )
    filter_levels: list[float] = Field(
        default=[1.0], title="Filter levels to apply to solved problem."
    )
    primal_method: str = Field(default="load_factor", title="Primal method")
    problem_name: str = Field(
        default="", title="Description of the problem being solved."
    )
    csv_filename: str = Field(
        default="results.csv",
        title="File to save results to, default is 'results.csv' (within 'output_dir', i.e. './output/results.csv')",
    )
    notes: str = Field(default="", title="Notes to add to the model.")
    plotting: dict[str, Any] = Field(
        default={"run": False, "bar_thickness": 0.3, "dpi": 1200},
        title="Plotting options.",
    )

    def __post_init__(self) -> None:
        """Post initialisation."""
        self.output_dir = (
            self.output_dir
            if isinstance(self.output_dir, Path)
            else Path(self.output_dir)
        )


@dataclass(
    repr=True,
    eq=True,
    config=ConfigDict(
        arbitrary_types_allowed=True, validate_assignment=True, frozen=True
    ),
    validate_on_init=True,
)
class CaseFamily:
    """
    A loading situation in which there is the potential for variability, e.g. which are favourable/unfavourable.

    Attributes
    ----------
    loaded_points : tuple[tuple(float)]
        A list of coordinates giving the points at which loads are to be applied.
    load_large : float
        The maximum load which may be applied at each point. For example, under eurocode design, this would correspond
        to the load factored using the unfavourable factors.
    load_small : float
        The minimum load which may be applied at each point. For example, under eurocode design, this would usually
        correspond to the load factored using the favourable factors.
    load_direction: tuple[float]
        A vector giving the direction of a positive force e.g. (0.0,1.0) for the y direction.
    """

    loaded_points: tuple[tuple[float]]
    load_large: float
    load_small: float
    load_direction: tuple[float]


@dataclass(
    repr=True,
    eq=True,
    config=ConfigDict(
        arbitrary_types_allowed=True, validate_assignment=True, frozen=True
    ),
    validate_on_init=True,
)
class Case:
    """
    A particular realisation of a loading situation, with a specific distribution of large and small loads.

    Attributes
    ----------
    activated : bool
        Whether this particular case is currently being considered in the reduced problem
    pattern : tuple[bool]
        For each loaded point (of the associated CaseFamily) is the force applied there the load_large (pattern[i]=True)
        or the load_small (pattern[i]=False).
    case_family : CaseFamily
        The parent CaseFamily that this case relates to.
    """

    activated: bool
    pattern: tuple[bool]
    case_family: CaseFamily

    def __hash__(self) -> int:
        """
        Define hash based on pattern.

        Returns
        -------
        int
            The hash of the pattern. (Note: this is deliberately not affected by the activated bool).
        """
        return hash(self.pattern)


@dataclass(
    repr=True,
    eq=True,
    config=ConfigDict(
        arbitrary_types_allowed=True, validate_assignment=True, frozen=True
    ),
    validate_on_init=True,
)
class Node:
    """
    A node is a point where one or more connections join.

    Attributes
    ----------
    coordinate : npt.NDArray[np.float64]
        The position of the node in Euclidean space.
    supported_dof : npt.NDArray[np.bool]
        Supported degrees of freedom.
    loading : dict[Case, list[float]]
        Loading of the node.
    virtual_displacements : dict[Case, list[float]]
        Displacements.
    """

    coordinate: npt.NDArray[np.float64]
    supported_dof: npt.NDArray[np.bool]
    loading: dict[Case, list[float]]
    virtual_displacements: dict[Case, list[float]]


@dataclass(
    repr=True,
    eq=True,
    config=ConfigDict(arbitrary_types_allowed=True, validate_assignment=True),
    validate_on_init=True,
)
class Connection:
    """
    Connections are the characteristics between two ``Node``.

    Attributes
    ----------
    start_node : Node | int
        The first of two ``Node`` the connection spans.
    end_node : Node | int
        The second of two ``Node`` the connection spans.
    activated : bool
        Whether the connection is currently being considered in the reduced problem (if solve has not started yet, this
        says whether the connection will be used in the first iteration, if solve has been completed, this says
        whether the connection was used in the final iteration).
    length : float
        Length of the connection between ``start_node`` and ``end_node``.
    """

    start_node: Node | int
    end_node: Node | int
    activated: bool
    length: float


@dataclass(
    repr=True,
    eq=True,
    config=ConfigDict(arbitrary_types_allowed=True, validate_assignment=True),
    validate_on_init=True,
)
class TrussBar(Connection):
    """
    A truss within a ``Structure``, extends the ``Connection`` class.

    Attributes
    ----------
    area : float, optional
        The cross-section area of the truss bar. If None, the bar was not considered in any iterations of the reduced
        problem.
    forces : dict[Case, float | None]
        The axial forces carried by the element in each of the active cases.
    stress_tensile : float
        The allowable stress of the element in tension.
    stress_compressive: float
        The allowable stress of the element in compression.
    """

    area: float | None
    forces: dict[Case, float | None]
    stress_tensile: float
    stress_compressive: float


@dataclass(
    repr=True,
    eq=True,
    config=ConfigDict(arbitrary_types_allowed=True, validate_assignment=True),
    validate_on_init=True,
)
class GrillageBeam(Connection):
    """
    A beam within a ``Structure``, extends the ``Connection`` class ``Structure()``.

    Attributes
    ----------
    start_web_area : float, optional
        The total area of the webs (i.e. the portion of the cross-section which is used to carry bending stresses) at
        the start_node.
    end_web_area : float, optional
        The total area of the webs (i.e. the portion of the cross-section which is used to carry bending stresses) at
        the end_node.
    flange_area : float, optional
        The area of the flange (i.e. the portion of the cross-section which is used to carry shear stresses). Note this
        is constant along the whole element.
    start_moments : dict[Case, float], optional
        The moments carried by the element at the start_node for each of the active cases.
    end_moments : dict[Case, float], optional
        The moments carried by the element at the end_node for each of the active cases.
    capacity_coeffiient_pos : float
        The area per unit moment required to carry positive (hogging) moments. Typically, this can be calculated using
        (allowable stress)*(vertical distance between flange centroids).
    capacity_coeffiient_neg : float
        The area per unit moment required to carry negative (sagging) moments. Typically, this can be calculated using
        (allowable stress)*(vertical distance between flange centroids).
    """

    start_web_area: float | None
    end_web_area: float | None
    flange_area: float | None
    start_moments: dict[Case, float] | None
    end_moments: dict[Case, float] | None
    capacity_coeffiient_pos: float
    capacity_coeffiient_neg: float


@dataclass(
    repr=True,
    eq=True,
    config=ConfigDict(arbitrary_types_allowed=True, validate_assignment=True),
    validate_on_init=True,
)
class Structure:
    """
    Over-arching dataclass for the structure being modelled.

    Attributes
    ----------
    parameters : Parameters
        Parameters for the structure.
    bounding_coordinates : list[list[int, int]]
        Bounding coordinates of the structure.
    polygon : Polygon
        Shapely polygon object of the structure.
    convex : bool
        Whether the structure is convex or not.
    nodes : npt.NDArray[np.float64]
        Two-dimensional nodes of the structure.
    dof : npt.NDArray[np.float64],
        Degrees of Freedom
    potential_members : npt.NDArray[np.float64]
        Potential members, with active points indicated.
    active_members : npt.NDArray[np.bool]
        Active members, a subset of `potential_members`, set after solving.
    primal_adaptivity : bool
        Indicator of primal adaptivity.
    load_case_active : npt.NDArray[np.bool]
        Indicates whether the corresponding load case is active or not.
    active_pattern_loads : list[npt.NDArray[np.float64]]
        A subset of `all_patterns` where load cases are active.
    """

    parameters: Parameters = Field(
        title="Parameters for the structure and modelling", init=True
    )
    bounding_coordinates: npt.NDArray[np.float64] = Field(
        title="Bounding coordinates", init=False
    )
    polygon: Polygon = Field(title="Polygon", init=False)
    convex: bool = Field(title="Convex", init=False)
    nodes: npt.NDArray[np.float64] = Field(title="Nodes", init=False)
    dof: npt.NDArray[np.float64] = Field(title="Degrees of Freedom", init=False)
    all_patterns: list[npt.NDArray[np.float64]] = Field(
        title="Loaded points", init=False
    )
    potential_members: npt.NDArray[np.float64] = Field(
        title="Potential members", init=False
    )
    active_members: npt.NDArray[np.float64] = Field(title="Active members", init=False)
    primal_adaptivity: bool = Field(title="Primal adaptivity", init=False)
    load_case_active: npt.NDArray[np.bool] = Field(
        title="Indicates whether the corresponding load case is active or not.",
        init=False,
    )
    active_pattern_loads: list[npt.NDArray[np.float64]] = Field(
        title="Loaded points", init=False
    )

    def __post_init__(self) -> None:
        """Post initialisation create the structure based on parameters."""
        self.bounding_coordinates = np.asarray(
            [
                [0, 0],
                [self.parameters.width, 0],
                [self.parameters.width, self.parameters.height],
                [0, self.parameters.height],
            ]
        )
        self.polygon = structure.make_polygon(self.bounding_coordinates)
        self.convex = self.polygon.convex_hull.area == self.polygon.area
        self.nodes = structure.create_nodes(
            width=self.parameters.width,
            height=self.parameters.height,
            polygon=self.polygon,
        )
        if self.parameters.loaded_points is None:
            self.parameters.loaded_points = structure.calc_default_loaded_points(
                width=self.parameters.width, height=self.parameters.height
            )
            logger.info(
                f"Loaded points not provided, calculated as : {self.parameters.loaded_points=}"
            )
        self.dof = structure.support_conditions(
            nodal_coords=self.nodes, support_points=self.parameters.support_points
        )
        self.all_patterns, _, _ = structure.make_pattern_loads(
            self.nodes,
            self.parameters.loaded_points,
            self.parameters.load_large,
            self.parameters.load_small,
            self.parameters.load_direction,
        )
        self.potential_members = structure.calc_potential_members(
            nodes=self.nodes,
            max_length=self.parameters.max_length,
            joint_cost=self.parameters.joint_cost,
            convex=self.convex,
            polygon=self.polygon,
            max_length_initial_ground_structure=self.parameters.max_length_initial_ground_structure,
        )
        self.active_members = self.potential_members[
            self.potential_members[:, 3] == True  # noqa: E712, pylint: disable=singleton-comparison
        ]
        self.primal_adaptivity, self.load_case_active = structure.primal_adaptivity(
            primal_method=self.parameters.primal_method,
            all_patterns_length=len(self.all_patterns),
        )
        self.active_pattern_loads = [
            self.all_patterns[k]
            for k in range(len(self.all_patterns))
            if self.load_case_active[k]
        ]

    def __str__(self) -> str:
        """
        Representation function for class attributes.

        Returns
        -------
        str
            Formatted statistics on ``Structure``.
        """
        return (
            f"Width             : {self.parameters.width}"
            f"Height            : {self.parameters.height}"
            f"Convex            : {self.convex}"
            f"Total nodes       : {len(self.nodes)}"
            f"Potential members : {len(self.potential_members)}"
            f"Joint cost        : {self.parameters.joint_cost}"
        )
