# python-devkit

The python repo-lifecycle devkit — workspace locking (`lock-python`), the preflight check runner, and the canonical ruff configuration with its sync verb and drift gate, per the tooling-consolidation program. Purely python-domain by charter: the CI runner floor (step wrapper, runner provisioning, git tags, OCI cache) lives in [`ci-devkit`](https://github.com/outernet-foundation/ci-devkit), which this package will depend on.

The package is `python_devkit` (src-layout under `src/python_devkit/`); all dependencies resolve from PyPI (`bashrun`, `pydantic`, `typer`; git-source pins only in scratch branches testing unreleased changes).

## Shape

Entry point (`[project.scripts]`): `lock-python` → `lock_python.py:app`. The command function doubles as the library API — consumer preflights import `lock_python` and call `lock_python(check=True)` directly.

`lock_python.py` regenerates a uv workspace's `uv.lock` plus per-service `pylock.toml` exports. Discovery: members of `[tool.uv.workspace]` in the root `pyproject.toml` that carry a `Dockerfile`; each gets `pylock.toml` (`--no-default-groups`) and one `pylock.<group>.toml` (`--only-group`) per non-`dev` dependency group. Redirect: a group matching a key of `[tool.python-devkit.lock-python] group-export-dirs` (glob → repo-relative directory) exports into that directory instead of the member's, once, deduplicated across members — the generalization of placeframe's neural-networks accelerator groups, which several members declare identically but only a non-member base image consumes. `--check` compares normalized exports against committed files and exits non-zero on any staleness.

## Constraints

- **The module surface is cross-repo Python API.** `python_devkit.lock_python.lock_python(check, root)` is contract: placeframe's preflight calls it in-process, its entry point is on CI's path, and the `[tool.python-devkit.lock-python]` table in consumer root pyprojects is its declarative config surface.
- **`group-export-dirs` is devkit-owned and `extra="forbid"`.** A typo'd key in that table fails validation loudly rather than silently dropping the redirect (the failure mode is per-group pylocks appearing in member directories).
- **The redirect contract assumes identical group declarations.** Dedup is first-member-wins; members declaring the same redirected group differently get whichever member enumerates first, silently.
- **Export commands are byte-stability load-bearing.** The exact `uv export` flag order must not churn — committed pylocks are compared byte-for-byte (after newline normalization), so a cosmetic flag change ripples into every consumer's diff.
- **uv invocations run with `cwd=root`.** `--root` (default: current directory) exists so the verb and the library call work from anywhere; the uv commands themselves must execute inside the workspace root.

## Release flow

`release.yml` (workflow_run-gated on CI) publishes via release-devkit uvx-isolated under OIDC trusted publishing (publisher bound to `release.yml`, no environment); the first release is 0.1.0 on the fresh `python-devkit-v*` tag ledger. The committed `pyproject.toml` version is permanently the `0.0.0.dev0` sentinel; the tags are the version ledger. API-breaking changes ship with a manually bumped version — patch-auto assumes additive changes.

## See also

- `README.md` — human-facing overview.
- [tooling-consolidation.md](https://github.com/outernet-foundation/placeframe/blob/dev/design/tooling-consolidation.md) — the program this repo belongs to.
