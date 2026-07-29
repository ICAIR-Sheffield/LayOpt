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

### Pre-releases

If you wish to try pre-releases, denoted by suffixes of the form `a#` for alpha releases, `b#` for beta and `rc#` for
release candidates you should include the specific version when calling `pip`. For example to install the `0.1.0a1`
(first alpha release of version 0.1.0) you would use...

``` shell
# Plain virtual environment
pip install layopt==0.1.0a1
# uv virtual environment
uv pip install layopt==0.1.0a1
```

## Rhino and Grasshopper Users

<!-- markdownlint-disable MD046 -->
!!! warning

    If you are using [Rhino](https://www.rhino3d.com/) and/or the [Grasshopper](https://www.grasshopper3d.com/)
    plugin/extension to run Python code then you may encounter some problems. The solutions to these are described
    below.
<!-- markdownlint-enable MD046 -->

### Minimum Python Version

LayOpt has been developed using a minimum Python version requirement of >= 3.12 due to the [end of life
scheduled][python_eol] for various versions. The current stable release of Rhino (8.0) only supports Python 3.9. The
developers are however targeting [Python 3.13][rhino_python] as the minimum version for the imminent Rhino 9.0 release
and the [Beta version][rhino_beta] already includes this support. You should therefore use the Beta version (or >= 9.0
once released) if you wish to use LayOpt.

### Locale Issues

Users have identified some [issues][rhino_locale] with setting `locales` when the [Pandas][pd] package is
imported. LayOpt uses Pandas to handle building data frames of results which are written to `.csv` output files and so
you may encounter this issue.

If you this issue then you should follow the advice in the [thread][rhino_locale] and set your `locale` explicitly to
`en_US` before explicitly importing `pandas`. Sample code from the linked thread is shown below.

```python
import locale

locale.setlocale(locale.LC_ALL, "en_US")

import pandas
```

If you encounter this problem and this doesn't resolve it please seek assistance in the [Rhino forums][rhino_forums].

## GitHub

You can use [`pip`][pip] to install the package directly from GitHub. This allows you to install a specific branch or
commit to test out new functionality that is under development. In your Virtual Environment run...

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
[pd]: https://pandas.pydata.org/
[pep8]: https://pep8.org/
[pip]: https://pip.pypa.io/en/stable/installation/
[precommit]: https://precommit.com/
[pypi]: https://pypi.org/
[python_eol]: https://devguide.python.org/versions/
[pyvenv]: https://realpython.com/python-virtual-environments-a-primer/
[rhino_beta]: https://discourse.mcneel.com/t/help-shape-rhino-9-the-beta-is-here/220246
[rhino_forums]: https://discourse.mcneel.com/
[rhino_locale]: https://discourse.mcneel.com/t/rhino-8-feature-scripteditor-cpython-csharp/128353/389
[rhino_python]: https://discourse.mcneel.com/t/rhino-beta-feature-python-3-13/205209
[uv]: https://docs.astral.sh/uv/
[uv_install]: https://docs.astral.sh/uv/getting-started/installation/
