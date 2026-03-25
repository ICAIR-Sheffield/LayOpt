"""Layopt plotting module."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy.typing as npt

plt.rcParams["figure.max_open_warning"] = 0


def plot_truss(
    nodal_coords: npt.NDArray,
    c_n: npt.NDArray,
    areas: npt.NDArray,
    forces: list,
    threshold: float,
    title: str,
    all_cases: bool = False,
    outfile: str | Path | None = None,
    img_ext: str = "png",
    dpi: int = 1200,
) -> tuple[plt.Figure, plt.Axes]:
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
    all_cases : bool
        Plot all load cases individually (default=``False``).
    outfile : str | Path | None
        If not ``None`` saves the image to the given filename.
    img_ext : str
        Image format to save as.
    dpi : int
        Dots Per Image for image resolution.

    Returns
    -------
    tuple[plt.Figure, plt.Axes]
        Matplotlib.pyplot figure and axes objects.
    """
    # ns-rse 2026-03-25: may want to remove plot_all_cases() and use recursion
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
        ax.axis("off")
        ax.axis("equal")
        ax.set_title(title)
        bar_thickness = 0.4  # bar thickness scale
        for i in [i for i in range(len(areas)) if areas[i] >= threshold]:
            if len(forces) > 1:  # multiple LC coloring
                print(f"\n{forces=}\n")
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
        fig.savefig(Path(outfile).with_suffix(img_ext), dpi=dpi)

    return fig, ax


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
    for k in enumerate(forces):
        plot_truss(
            nodal_coords=nodal_coords,
            c_n=c_n,
            areas=areas,
            forces=[forces[k]],
            threshold=threshold,
            title=stress_tensile + " case " + str(k),
            all_cases=False,
        )
