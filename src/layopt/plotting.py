"""Layopt plotting module."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt

if TYPE_CHECKING:
    import numpy as np
    import numpy.typing as npt

plt.rcParams["figure.max_open_warning"] = 0


def plot_truss(
    nodal_coords: npt.NDArray[np.float64],
    c_n: npt.NDArray[np.float64],
    areas: npt.NDArray[np.float64],
    forces: list[npt.NDArray[np.float64]],
    threshold: float,
    title: str,
    outfile: str | Path | None = "truss",
    img_ext: str = ".png",
    bar_thickness: float = 0.3,
    dpi: int = 1200,
) -> tuple[plt.Figure, plt.Axes]:
    """
    Visualise truss.

    Parameters
    ----------
    nodal_coords : npt.NDArray
        Nodal coordinates.
    c_n : npt.NDArray[np.float64]
        Active members.
    areas : npt.NDArray[np.float64]
        Member areas.
    forces : list[npt.NDArray[np.float64]]
        Member forces.
    threshold : float
        Minimum allowable member area.
    title : str
        Title for plot, typically includes the filter level expressed as a percentage.
    outfile : str | Path | None
        If not ``None`` saves the image to the given filename.
    img_ext : str
        Image format to save as.
    bar_thickness : float
        Bar thickness.
    dpi : int
        Dots Per Image for image resolution.

    Returns
    -------
    tuple[plt.Figure, plt.Axes]
        Matplotlib.pyplot figure and axes objects.
    """
    fig = plt.figure()
    ax = fig.subplots()
    ax.axis("off")
    ax.axis("equal")
    ax.set_title(title)
    for i in [i for i in range(len(areas)) if areas[i] >= threshold]:
        # for i in [i for i in areas if i >= threshold]:
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
    if outfile is not None:
        # Strip any extension from outfile and replace with img_ext when saving the file
        img_ext = "." + img_ext if img_ext[0] != "." else img_ext
        outfile = (
            Path(outfile).parent / Path(outfile).stem
            if outfile is not None
            else "truss"
        )
        fig.savefig(Path(outfile).with_suffix(img_ext), dpi=dpi)

    return fig, ax


def plot_all_cases(
    nodal_coords: npt.NDArray[np.float32],
    c_n: npt.NDArray[np.float32],
    areas: npt.NDArray[np.float32],
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
    for k in enumerate(forces):
        plot_truss(
            nodal_coords=nodal_coords,
            c_n=c_n,
            areas=areas,
            forces=[forces[k]],
            threshold=threshold,
            title=stress_tensile + " case " + str(k),
        )
