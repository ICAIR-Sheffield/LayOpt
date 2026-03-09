# LayOpt

[![Actions Status][actions-badge]][actions-link]
[![Documentation Status][rtd-badge]][rtd-link]

[![PyPI version][pypi-version]][pypi-link]
[![Conda-Forge][conda-badge]][conda-link]
[![PyPI platforms][pypi-platforms]][pypi-link]

[![GitHub Discussion][github-discussions-badge]][github-discussions-link]

[![Coverage][coverage-badge]][coverage-link]

# LayOpt

LayOpt is a Python package for topology optimisation of fail-safe trusses
developed by the [Integrated Civil and Infrastructure Research Centre][icair] at
[The University of Sheffield][tuos].

## Installation

### PyPI

**LayOpt** is not yet published to PyPI, for now you will have to install from
GitHub.

### GitHub

You can use [`pip`][pip] to install the package directly from GitHub. In your
Virtual Environment run...

```shell
# Install from HEAD of main branch
pip install git@https://github.com/ICAIR-Sheffield/LayOpt
# Install a specific <branch>
pip install git@https://github.com/ICAIR-Sheffield/LayOpt.git@<branch>
```

### Development

Contributions are welcome. If you are considering contributing to the
development of LayOpt and are not a collaborator of the repository then you
should fork to your account first and then clone from there.

We use [uv][uv] package manager to develop LayOpt. To install this software
clone the repository and make sure you have [uv installed][uv_install].

```shell
# Clone using SSH
git clone git@github.com:ICAIR-Sheffield/LayOpt.git
# Clone using https
git clone https://github.com/ICAIR-Sheffield/LayOpt.git
# Change directory
cd LayOpt
# Create a virtual Environment
uv venv
# Synchronise the virtual environment (installs dependencies)
uv sync
# Install the package...
uv sync
# Install development dependencies
uv pip install --group dev
```

## Documentation

We use the [mkdocs][mkdocs] static site generator to build a website. This is
deployed on both ReadTheDocs and GitHub Pages.

- [ReadTheDocs][rtd-link]
- [GitHub Pages][gh-pages-link]

## Citing

To cite this software please refer to the `CITATION.cff` included in this
repository.

<!-- prettier-ignore-start -->
[actions-badge]:            https://github.com/ICAIR-Sheffield/LayOpt/workflows/CI/badge.svg
[actions-link]:             https://github.com/ICAIR-Sheffield/LayOpt/actions
[conda-badge]:              https://img.shields.io/conda/vn/conda-forge/LayOpt
[conda-link]:               https://github.com/conda-forge/LayOpt-feedstock
[gh-pages-link]:            https://ICAIR-Sheffield.github.io/LayOpt
[github-discussions-badge]: https://img.shields.io/static/v1?label=Discussions&message=Ask&color=blue&logo=github
[github-discussions-link]:  https://github.com/ICAIR-Sheffield/LayOpt/discussions
[icair]:                    https://icair.ac.uk/
[mkdocs]:                   https://www.mkdocs.org/
[pypi-link]:                https://pypi.org/project/LayOpt/
[pypi-platforms]:           https://img.shields.io/pypi/pyversions/LayOpt
[pypi-version]:             https://img.shields.io/pypi/v/LayOpt
[rtd-badge]:                https://readthedocs.org/projects/LayOpt/badge/?version=latest
[rtd-link]:                 https://LayOpt.readthedocs.io/en/latest/?badge=latest
[tuos]:                     https://www.sheffield.ac.uk/
[uv]:                       https://docs.astral.sh/uv/
[uv_install]:               https://docs.astral.sh/uv/getting-started/installation/
[coverage-badge]:           https://codecov.io/github/ICAIR-Sheffield/LayOpt/branch/main/graph/badge.svg
[coverage-link]:            https://codecov.io/github/ICAIR-Sheffield/LayOpt

<!-- prettier-ignore-end -->
