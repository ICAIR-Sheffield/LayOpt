"""Tests of the plotting module."""

from pathlib import Path
from typing import Any

import pytest

from layopt import plotting  # type: ignore[import-not-found]


@pytest.mark.mpl_image_compare(baseline_dir="__mpl_snapshots__")
@pytest.mark.parametrize(
    (
        "structure_fixture",
        "plotting_data_fixture",
        "all_cases",
        "outfile",
        "img_ext",
        "title",
    ),
    [
        pytest.param(
            "input_one_by_one",
            "plotting_data_one_by_one",
            False,
            None,
            "png",
            "1x1 test",
            id="1x1 plot",
        ),
        pytest.param(
            "input_two_by_two",
            "plotting_data_two_by_two",
            False,
            None,
            "png",
            "2x2 test",
            id="2x2 plot",
        ),
        pytest.param(
            "input_three_by_six",
            "plotting_data_three_by_six_short_cantilever",
            False,
            None,
            "png",
            "3x6 test",
            id="3x6 plot",
        ),
    ],
)
def test_plot_truss(
    structure_fixture: str,
    plotting_data_fixture: str,
    all_cases: bool,
    outfile: Path,
    img_ext: str,
    title: str,
    request,
) -> Any:
    """Test for ``plotting.plot_truss()``."""
    structure = request.getfixturevalue(structure_fixture)
    plotting_data = request.getfixturevalue(plotting_data_fixture)
    fig, _ = plotting.plot_truss(
        nodal_coords=structure["nodal_coords"],
        c_n=structure["c_n"],
        areas=plotting_data["areas"],
        forces=plotting_data["forces"],
        threshold=plotting_data["threshold"],
        all_cases=all_cases,
        title=title,
        outfile=outfile,
        img_ext=img_ext,
    )
    return fig
