# python-devkit

Python repo-lifecycle tooling shared across outernet-foundation repos: the CI step wrapper (`ci_step`), CI runner provisioning (`configure_git`, `free_disk_space`, `install_dotnet`, `install_node`, `install_oras`), and — as the program progresses — workspace locking, the preflight check runner, and the canonical ruff configuration. Sibling of `unity-devkit`, `docker-devkit`, and `release-devkit` in the `-devkit` family; `bashrun` and `logger-conf` stay standalone.

## Setup

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Consuming from another repo

```toml
[project]
dependencies = ["python-devkit>=0.1.0"]
```

```python
from python_devkit.ci_step import ci_step
from python_devkit.setup import configure_git, free_disk_space, install_dotnet, install_node
from python_devkit.setup_oras import install_oras
```

To test an unreleased change, pin the repo at a git ref in a scratch branch instead (`python-devkit = { git = "…", rev = "<sha>" }` under `[tool.uv.sources]`) and drop the pin when the release lands.

## Development

```bash
uv run ruff check .
uv run ruff format --check .
uv run basedpyright
```
