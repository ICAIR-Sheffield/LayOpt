# Installation

## PyPI

**LayOpt** is not yet published to PyPI, for now you will have to install from GitHub.

## GitHub

You can use [`pip`][pip] to install the package directly from GitHub. In your Virtual Environment run...

```shell
# Install from HEAD of main branch
pip install git@https://github.com/ICAIR-Sheffield/LayOpt
# Install a specific <branch>
pip install git@https://github.com/ICAIR-Sheffield/LayOpt.git@<branch>
```

## Development

Contributions are welcome. If you are considering contributing to the development of LayOpt and are not a collaborator
of the repository then you should fork to your account first and then clone from there.

We use [uv][uv] package manager to develop LayOpt. To install this software clone the repository and make sure you have
[uv installed][uv_install].

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
# Install development dependencies
uv pip install --group dev
# Install pre-commit hooks
pre-commit install
```

[pip]: https://pip.pypa.io/en/stable/installation/
[uv]: https://docs.astral.sh/uv/
[uv_install]: https://docs.astral.sh/uv/getting-started/installation/
