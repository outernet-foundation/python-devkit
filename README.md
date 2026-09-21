# python-devkit

Python repo-lifecycle tooling shared across outernet-foundation repos: workspace locking (`lock-python`), the preflight check runner, and the canonical ruff configuration with its sync verb and drift gate. Sibling of `ci-devkit` (the CI runner floor it will depend on), `unity-devkit`, `docker-devkit`, and `release-devkit`.

## lock-python

Regenerates a uv workspace's `uv.lock` and the per-service `pylock.toml` exports consumed by service Dockerfiles:

```bash
uv run lock-python           # write: uv lock + every export
uv run lock-python --check   # validate; exit 1 on any stale lock
```

For every workspace member that carries a `Dockerfile`, it exports `pylock.toml` (no default groups) plus one `pylock.<group>.toml` per non-`dev` dependency group. Dependency groups whose names match a pattern in the root `pyproject.toml`'s `[tool.python-devkit.lock-python] group-export-dirs` map export into the mapped directory instead, once, deduplicated across members — e.g. placeframe's accelerator groups:

```toml
[tool.python-devkit.lock-python]
group-export-dirs = { "neural-networks-*" = "docker/neural-networks-base" }
```

## preflight runner

Consumer preflights thin into a declarative check list over `run_checks`:

```python
from python_devkit.preflight_runner import CommandCheck, GeneratedCheck, run_checks

run_checks([
    CommandCheck(label="Lint", command="uv run ruff check ."),
    GeneratedCheck(
        label="Check client codegen",
        generate_command="uv run generate-clients",
        paths=[Path("packages/generated/")],
        fix_command="uv run generate-clients",
    ),
])
```

`CommandCheck` wraps a shell command in a labeled CI step group; `GeneratedCheck` additionally guards the checked-in generator output with a git-status staleness check (diff shown, fix command named). Checks run fail-fast with per-step durations in the Actions step summary.

## Development

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run ruff check .
uv run ruff format --check .
uv run basedpyright
```
