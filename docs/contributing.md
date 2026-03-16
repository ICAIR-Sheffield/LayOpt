# Contributing

Contributions to the project are welcome. If you are not a collaborator on the GitHub repository then you should fork
the repository, make your changes on the fork and then create a Pull Request. Collaborators can clone and make
contributions directly, although the `main` branch is protected so all changes should be made on dedicated branches and
a Pull Request used to merge the changes to the `main` branch.

## Git

### Branches

Please use structured branch names which impart metadata about who the branch belongs to and what issue is being
addressed. The suggested structure is `<github_username>/<issue_number>-<short_text_description>`, e.g.
`ns-rse/10-integration-test` is a branch created by `ns-rse` addressing issue `10` which introduces `integration-test`
to the code base.

### Commits

We advocate the use of [Conventional Commits][conventional_commit] which provides a structured nomenclature for writing
your commit messages. We would also encourage the use of multi-line commit messages rather than a single header so that
more detailed information on _why_ something has been done in a certain way is recorded against commits.

## Style

We employ [pre-commit][pre-commit] hooks to apply a number of linting, type-hints and style rules using the following
tools.

- [black][black]
- [codespell][codespell]
- [numpydoc][numpydoc_validation]
- [mypy][mypy]
- [prettier][prettier]
- [pylint][pylint]
- [ruff][ruff]

If you follow the [development installation instructions](installation.md#development) you should have all necessary
tools installed and find that your IDE recognises and uses some of these automatically.

## Virtual Environments

It is recommended that you use [Virtual Environments][venv] to install the LayOpt package and its dependencies. We use
[uv][uv] and recommend it. After [installing uv][uv_install] you will need to create a virtual environment, synchronise
and install the package.

```shell
# Change directory to where LayOpt is cloned
cd ~/path/to/LayOpt
# Create a virtual environment with uv
uv env
# Synchronise and install the package and its dependencies
uv sync
# Install the development packages
uv pip install --group dev
```

## Pre-commit

The [pre-commit][pre-commit] hooks need installing after you have installed the development packages

```shell
pre-commit install
```

You should now find that the pre-commit hooks run before each commit is made. If the hooks do not pass then the commit
will fail (although this can be over-ridden at the command line using the `-n` flag).

## Linting and Style

Using a consistent style to write code means its easier to read and understand both your own and others code. The widely
accepted [PEP8][pep8] style guide is used by the LayOpt code base and [numpydoc][numpydoc] for formatting of docstrings.

[black]: https://black.readthedocs.io/en/stable/
[codespell]: https://github.com/codespell-project/codespell
[conventional_commit]: https://www.conventionalcommits.org/en/v1.0.0/
[numpydoc]: https://numpydoc.readthedocs.io/en/latest/
[numpydoc_validation]: https://numpydoc.readthedocs.io/en/latest/validation.html
[mypy]: https://www.mypy-lang.org/
[pep8]: https://peps.python.org/pep-0008/
[pre-commit]: https://pre-commit.com/
[prettier]: https://prettier.io/
[pylint]: https://pylint.readthedocs.io/en/stable/
[ruff]: https://docs.astral.sh/ruff/
[uv]: https://docs.astral.sh/uv/
[uv_install]: https://docs.astral.sh/uv/getting-started/installation/
[venv]: https://docs.python.org/3/library/venv.html
