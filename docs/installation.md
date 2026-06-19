# Installation

There are a number of different options for installing LayOpt depending on whether you want to just use a stable
release, a development version or contribute to development.

Once installed please refer to the [usage instructions](usage.md).

## Virtual Environment

It is recommended that you use a [Python Virtual Environment][pyvenv] to install LayOpt. There are many options
available but a good choice, used in the development of LayOpt, is [uv][uv]. Create a directory for your work and after
[installing uv][uv_install] create a virtual environment.

```shell
# Create a directory
mkdir LayOpt
# Change directory
cd LayOpt
# Create a virtual Environment
uv venv
```

## PyPI

Released versions are available for installation from [PyPI][pypi]. Ideally you should use a Python Virtual Environment
(see above).

```shell
# Plain virtual environment
pip install layopt
# uv virtual environment
uv pip install layopt
```

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

### Style and Linting

We use a number of [pre-commit][precommit] hooks to ensure the codebase follows the [PEP8][pep8] style guide and
functions/methods, classes and modules are documented using [numpydoc Style][numpydoc]. After installing the pre-commit
hooks you will find when making a commit that the hooks are run against the changes being submitted. Sometimes the hooks
will reformat the files to ensure they follow the guidelines, but not all changes can, or should, be applied
automatically and you will have to review the output and make the changes, stage and commit (`--amend`) to ensure the
hooks pass.

Of particular note is ensuring the typehints are consistent as we use [mypy][mypy] to run static type checking against
the code base. For details of all hooks used see the `.pre-commit-config.yaml` file in the repository.

[mypy]: https://mypy.readthedocs.io/en/stable/getting_started.html
[numpydoc]: https://numpydoc.readthedocs.io/en/latest/format.html
[pep8]: https://pep8.org/
[pip]: https://pip.pypa.io/en/stable/installation/
[precommit]: https://precommit.com/
[pypi]: https://pypi.org/
[pyvenv]: https://realpython.com/python-virtual-environments-a-primer/
[uv]: https://docs.astral.sh/uv/
[uv_install]: https://docs.astral.sh/uv/getting-started/installation/
