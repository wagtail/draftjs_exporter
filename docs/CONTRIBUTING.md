# Contribution Guidelines

Thank you for considering to help this project.

We welcome all support, whether on bug reports, code, design, reviews, tests, documentation, and more. Check out the [project roadmap](../ROADMAP.md) for high-level ideas that align with the project’s goals.

Please note that this project is released with a [Contributor Code of Conduct](docs/CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.

## Development

### Installation

> Requirements: [`uv`](https://github.com/astral-sh/uv)

Clone the repository, configure the git hooks, then initialize with `just init`.

```sh
git clone git@github.com:wagtail/draftjs_exporter.git
cd draftjs_exporter/
# Install the git hooks.
./.githooks/deploy
# Install the Python environment.
just init
```

### Commands

- `just help`: See what commands are available.
- `just init`: Install dependencies and initialise for development.
- `just lint`: Lint the project.
- `just format`: Format project files.
- `just test`: Test the project.
- `just test-watch`: Restarts the tests whenever a file changes.
- `just test-coverage`: Run the tests while generating test coverage data.
- `just test-compatibility`: Compatibility-focused test suite.
- `just dev`: Restarts the example whenever a file changes.
- `just benchmark`: Runs a one-off performance (speed, memory) benchmark.
- `just clean-pyc`: Remove Python file artifacts.
- `just build`: Builds package for publication.
- `just publish`: Publishes a new version to PyPI.

### Debugging

- Always run the tests. To auto-run with watch, use `npm install -g nodemon`, then `just test-watch`.
- Use a debugger. `uv pip install ipdb`, then `import ipdb; ipdb.set_trace()`.
- You can use `example.py` as a basic CLI to try out the exporter with arbitrary ContentState JSON: `echo '{"json": "contents"}' | ./example.py -`.

### Releases

- Make a new branch for the release of the new version.
- Update the [CHANGELOG](https://github.com/wagtail/draftjs_exporter/CHANGELOG.md).
- Update the version number in `pyproject.toml`, following semver.
- Update the version number in `draftjs_exporter/__init__.py`, following semver.
- Make a PR and squash merge it.
- Back on main with the PR merged, use `just publish` (confirm, and enter your password).
- Finally, go to GitHub and create a release and a tag for the new version.
- Done!

> As a last step, you may want to go update the [Draftail Playground](http://playground.draftail.org/) to this new release to check that all is well in a fully separate project.

## Support guidelines

### Python versions support

- Official support for [supported Python versions](https://devguide.python.org/versions/), communicated via trove classifiers and in the README, tested in CI.
- Tentative support for upcoming Python versions, tested in CI to some degree.
- Case-by-case, unofficial undocumented support for end-of-life Python versions.

### Benchmarks

Consider [building Python for maximum performance](https://github.com/pyenv/pyenv/blob/master/plugins/python-build/README.md#building-for-maximum-performance):

```sh
env PYTHON_CONFIGURE_OPTS='--enable-optimizations --with-lto' PYTHON_CFLAGS='-march=native -mtune=native' pyenv install 3.6.0
```

### Static typing

All exporter code should pass static type checking by [mypy](https://mypy.readthedocs.io/en/latest/index.html), with as strict of a configuration as possible, and tentatively also pass type checks with the [ty](https://docs.astral.sh/ty/) checker.

## Documentation

> See the [docs](https://github.com/wagtail/draftjs_exporter/tree/main/docs) folder.
