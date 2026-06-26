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

## Linting and Style

Using a consistent style to write code means it's easier to read and understand both your own and others code. The
widely accepted [PEP8][pep8] style guide is used by the LayOpt code base and [numpydoc][numpydoc] for formatting of
docstrings. These are enforced on the code base using [Pre-commit](#pre-commit) hooks and you are encouraged to install
and use these hooks when committing your work.

## Pre-commit

We employ [pre-commit][pre-commit], a framework for running checks on data prior to making commits, and apply a number
of linting, type-hints and style rules using the following tools.

- [black][black]
- [codespell][codespell]
- [numpydoc][numpydoc_validation]
- [mypy][mypy]
- [prettier][prettier]
- [pylint][pylint]
- [ruff][ruff]

If you follow the [development installation instructions](installation.md#development) you should have all necessary
tools installed and find that your IDE recognises and uses some of these automatically. If you have already cloned the
repository then you can install the Pre-commit hooks with:

```shell
pre-commit install
```

You should now find that the pre-commit hooks run before each commit is made. If the hooks do not pass then the commit
will fail. We encourage the use of pre-commit hooks to check your commits but once installed they can be over-ridden at
the Git command line by using the `-n` flag). The hooks also run in the Continuous Integration that is triggered when
pull requests are created and errors there will be highlighted and need fixing prior to approving and merging pull
requests.

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
