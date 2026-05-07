"""Dataclass definitions."""

from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt
from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass


@dataclass(
    repr=True,
    eq=True,
    config=ConfigDict(arbitrary_types_allowed=True, validate_assignment=True),
    validate_on_init=True,
)
class Parameters:
    """Modelling parameters."""

    width: int = Field(default=3, title="Width of structure.", ge=1)
    height: int = Field(default=6, title="Height of structure.", ge=1)
    stress_tensile: float = Field(
        default=1.0, title="Tensile stress.", ge=0.0, le=1000.0
    )
    stress_compressive: float = Field(
        default=1.0, title="Compressive stress.", ge=0.0, le=1000.0
    )
    joint_cost: float = Field(default=0.0, title="Joint cost.", ge=0.0, le=1000.0)
    loaded_points: npt.NDArray[np.int64] = Field(
        default=np.asarray([[3, 3]]), title="Loaded Points."
    )
    load_direction: tuple[float, float] = Field(
        default=(0.0, -1.0), title="Loaded direction."
    )
    load_large: float = Field(default=50.0, title="Maximum length.", ge=0.0, le=1000.0)
    load_small: float = Field(default=5.0, title="Maximum length.", ge=0.0, le=1000.0)
    max_length: float = Field(default=18.0, title="Maximum length.", ge=0.0, le=1000.0)
    support_points: npt.NDArray[np.float32] = Field(
        default=np.asarray([[3, 3]]), title="Support Points."
    )
    primal_method: str = Field(default="load_factor", title="Primal method")
    problem_name: str = Field(
        default="", title="Description of the problem being solved."
    )
    log_level: str = Field(default="info", title="Log level")
    notes: str = Field(default="", title="Notes to add to the model.")
    output_dir: str | Path = Field(
        default="./output/", title="Path to save the output to, default is './output/'."
    )
    plotting: dict[str, Any] = Field(
        default={"run": False, "bar_thickness": 0.3, "dpi": 1200},
        title="Plotting options.",
    )
    filter_levels: list[float] = Field(
        default=[1.0], title="Filter levels to apply to solved problem."
    )
    cores: int = Field(default=2, title="Cores to run optimisation on in parallel.")
    csv_filename: str = Field(
        default="results.csv",
        title="File to save results to, default is 'results.csv' (within 'output_dir', i.e. './output/results.csv')",
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
    Definition required.

    Attributes
    ----------
    loaded_points : tuple[tuple(float)]
        Definition required.
    load_large : float
        Definition required.
    load_small : float
        Definition required.
    load_direction: tuple[float]
        Definition required.
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
    Definition required.

    Attributes
    ----------
    activated : bool
        Definition required.
    pattern : tuple[bool]
        Definition required.
    case_family : CaseFamily
        Definition required.
    """

    activated: bool
    pattern: tuple[bool]
    case_family: CaseFamily


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
        The position of the node Euclidean space.
    supported_dof : npt.NDArray[np.bool]
        Supported degrees of freedom.
    loading : dict[str, Case]
        Loading of the node.
    virtual_displacements : dict[str, Case]
        Displacements.
    """

    coordinate: npt.NDArray[np.float64]
    supported_dof: npt.NDArray[np.bool]
    loading: dict[Case, list[float]]
    virtual_displacements: dict[Case, list[float | None]]


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
    elements : list
        Definition required.
    nodes : list[Node]
        A list of ``Node`` within the structure.
    cases : list[Case]
        A list of ``Case`` within the structure.
    joint_cost : float
        Joint cost.
    """

    elements: list[Any]
    nodes: list[Node]
    cases: list[Case]
    joint_cost: float

    def __str__(self) -> str:
        """
        Representation function for class attributes.

        Returns
        -------
        str
            Formatted statistics on ``Structure``.
        """
        return (
            f"Total elements : {len(self.elements)}"
            f"Total nodes : {len(self.nodes)}"
            f"Total cases : {len(self.cases)}"
            f"Joint cost : {self.joint_cost}"
        )


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
        Definition required.
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
        Definition required.
    forces : dict[str, Optional[float]]
        Definition required.
    stress_tensile : float
        Definition required.
    stress_compressive: float
        Definition required.
    """

    area: float | None
    forces: dict[str, float | None]
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
        Definition required.
    end_web_area : float, optional
        Definition required.
    flange_area : float, optional
        Definition required.
    start_moments : dict[str, Optional[Case | float]]
        Definition required.
    end_moments : dict[str, Optional[Case | float]]
        Definition required.
    capacity_coeffiient_pos : float
        Definition required.
    capacity_coeffiient_neg : float
        Definition required.
    """

    start_web_area: float | None
    end_web_area: float | None
    flange_area: float | None
    start_moments: dict[str, Case | float | None]
    end_moments: dict[str, Case | float | None]
    capacity_coeffiient_pos: float
    capacity_coeffiient_neg: float
