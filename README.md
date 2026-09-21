# python-devkit

Python repo-lifecycle tooling shared across outernet-foundation repos: workspace locking (`lock-python`), the preflight check runner, and the canonical ruff configuration with its sync verb and drift gate. Sibling of `ci-devkit` (the CI runner floor it will depend on), `unity-devkit`, `docker-devkit`, and `release-devkit`.

The package carries no content yet; it publishes once its first module lands.

## Development

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run ruff check .
uv run ruff format --check .
uv run basedpyright
```
