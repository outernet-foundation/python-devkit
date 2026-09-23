# python-devkit

Python repo-lifecycle tooling shared across outernet-foundation repos: workspace locking (`lock-python`), the preflight verb (the fixed Python battery), and the canonical ruff configuration with its sync verb and drift gate. Sibling of `ci-devkit` (the CI runner floor it depends on), `unity-devkit`, `docker-devkit`, and `release-devkit`.

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

## preflight

The fixed battery of checks every healthy org Python repo passes — the same command in CI and locally, fail-fast with per-step durations in the Actions step summary:

```bash
uvx --from python-devkit preflight-python   # sync → lint → format → types → deptry → lock staleness → ruff drift → tests
```

The battery is fixed by design: sync, ruff check, ruff format --check, basedpyright, deptry (pinned internally, so adoption adds no dependency), lock staleness (`lock-python --check` semantics; plain `uv lock --check` for non-workspace repos), ruff config drift, and pytest. For workspaces, deptry runs per `[tool.uv.workspace]` member that has a `pyproject.toml`, inside the member directory. Configuration is toggles only, in the root `pyproject.toml`:

```toml
[tool.python-devkit.preflight]
tests = false                    # skip pytest (default true)
sync-args = ["--all-packages"]   # extra flags for the sync step
deptry-exclude = ["packages/generated/*"]  # member-path globs skipped by the deptry step
```

Repo-specific checks (codegen staleness, environment setup) compose locally around the battery — `from python_devkit.preflight import preflight` and call it in-process — never inside python-devkit.

## ruff canonical config

`src/python_devkit/ruff.base.toml` is the org-canonical ruff configuration. Consuming repos carry it verbatim as `ruff.base.toml` at their root, with a hand-owned `ruff.toml` beside it layering repo-local deltas on top:

```bash
uvx --from python-devkit sync-ruff           # write/refresh ruff.base.toml
uvx --from python-devkit sync-ruff --check   # drift gate: exit 1 on divergence
```

The consuming `ruff.toml` must set `extend = "ruff.base.toml"` and may only add via extend keys (`extend-exclude`, `lint.extend-ignore`, `lint.extend-per-file-ignores`) — plain `exclude`, `lint.select`, `lint.ignore`, and `lint.per-file-ignores` replace the canonical settings under `extend`, and `--check` fails on them. To change the canonical: edit it here, release, and run `sync-ruff` in every consuming repo.

## CI check job

Consumers inline the check job directly in their `ci.yml`: checkout, cached uv setup, and one invocation of the preflight battery. The `python-devkit` version pin lives in each consumer's workflow file. Repo-specific toggles (`tests`, `sync-args`, `deptry-exclude`) live in each repo's `[tool.python-devkit.preflight]` table, not in workflow inputs.

```yaml
jobs:
  check:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v5

      - uses: astral-sh/setup-uv@v7
        with:
          enable-cache: true

      - name: Preflight
        run: uvx --from python-devkit==<pin> preflight-python
```

## Development

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run preflight-python
```
