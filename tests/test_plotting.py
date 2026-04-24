"""Tests of the plotting module."""

from pathlib import Path
from typing import Any

import pytest

from layopt import plotting  # type: ignore[import-not-found]


@pytest.mark.mpl_image_compare(baseline_dir="__mpl_snapshots__")
@pytest.mark.parametrize(
    (
        "plotting_data_fixture",
        "outfile",
        "img_ext",
        "title",
        "expected_file",
    ),
    [
        pytest.param(
            "plotting_data_one_by_one",
            "output",
            "png",
            "1x1 test",
            "output.png",
            id="1x1 plot outfile = output.png",
        ),
        pytest.param(
            "plotting_data_two_by_two",
            "truss",
            ".png",
            "2x2 test",
            "truss.png",
            id="2x2 plot outfile = truss.png",
        ),
        pytest.param(
            "plotting_data_three_by_six_short_cantilever",
            "another_plot",
            "svg",
            "3x6 test",
            "another_plot.svg",
            id="3x6 plot outfile = another_plot.svg",
            marks=pytest.mark.skip(
                reason="Awaiting update/simplification of 3x6 cantilever see #61"
            ),
        ),
    ],
)
def test_plot_truss(
    plotting_data_fixture: str,
    outfile: Path,
    img_ext: str,
    title: str,
    tmp_path: Path,
    expected_file: str,
    request,
) -> Any:
    """Test for ``plotting.plot_truss()``."""
    plotting_data = request.getfixturevalue(plotting_data_fixture)
    fig, _ = plotting.plot_truss(
        nodal_coords=plotting_data["nodal_coords"],
        c_n=plotting_data["c_n"],
        areas=plotting_data["areas"],
        forces=plotting_data["forces"],
        threshold=plotting_data["threshold"],
        title=title,
        outfile=tmp_path / outfile,
        img_ext=img_ext,
    )
    assert Path(tmp_path / expected_file).is_file()
    return fig
