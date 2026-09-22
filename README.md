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

## ruff canonical config

`src/python_devkit/ruff.base.toml` is the org-canonical ruff configuration. Consuming repos carry it verbatim as `ruff.base.toml` at their root, with a hand-owned `ruff.toml` beside it layering repo-local deltas on top:

```bash
uvx --from python-devkit sync-ruff           # write/refresh ruff.base.toml
uvx --from python-devkit sync-ruff --check   # drift gate: exit 1 on divergence
```

The consuming `ruff.toml` must set `extend = "ruff.base.toml"` and may only add via extend keys (`extend-exclude`, `lint.extend-ignore`, `lint.extend-per-file-ignores`) — plain `exclude`, `lint.select`, `lint.ignore`, and `lint.per-file-ignores` replace the canonical settings under `extend`, and `--check` fails on them. To change the canonical: edit it here, release, and run `sync-ruff` in every consuming repo.

## reusable check workflow

`.github/workflows/check.yml` is the org's reusable Python CI check (`workflow_call`): checkout, cached uv setup, `ruff check` + `ruff format --check`, `basedpyright`, `pytest` behind a `test` input (default true), and the ruff drift gate. Tool repos collapse their check jobs onto it, pinned to a pushed SHA:

```yaml
jobs:
  check:
    uses: outernet-foundation/python-devkit/.github/workflows/check.yml@<pushed-sha>
```

Pass `test: false` when the repo has no pytest suite. The drift gate's `python-devkit` version pin lives inside the workflow — bumping it is one edit here plus a SHA bump at consumers, never a per-repo edit wave.

## Development

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run ruff check .
uv run ruff format --check .
uv run basedpyright
```
