# python-devkit

The python repo-lifecycle devkit — workspace locking (`lock-python`), the preflight check runner, the canonical ruff configuration with its sync verb and drift gate, and the org's reusable Python check workflow, per the tooling-consolidation program. Purely python-domain by charter: the CI runner floor (step wrapper, runner provisioning, git tags, OCI cache) lives in [`ci-devkit`](https://github.com/outernet-foundation/ci-devkit), which this package depends on (`ci-devkit>=0.1.0`).

The package is `python_devkit` (src-layout under `src/python_devkit/`); all dependencies resolve from PyPI (`bashrun`, `ci-devkit`, `pydantic`, `typer`; git-source pins only in scratch branches testing unreleased changes).

## Shape

Entry point (`[project.scripts]`): `lock-python` → `lock_python.py:app`. The command function doubles as the library API — consumer preflights import `lock_python` and call `lock_python(check=True)` directly.

`lock_python.py` regenerates a uv workspace's `uv.lock` plus per-service `pylock.toml` exports. Discovery: members of `[tool.uv.workspace]` in the root `pyproject.toml` that carry a `Dockerfile`; each gets `pylock.toml` (`--no-default-groups`) and one `pylock.<group>.toml` (`--only-group`) per non-`dev` dependency group. Redirect: a group matching a key of `[tool.python-devkit.lock-python] group-export-dirs` (glob → repo-relative directory) exports into that directory instead of the member's, once, deduplicated across members — the generalization of placeframe's neural-networks accelerator groups, which several members declare identically but only a non-member base image consumes. `--check` compares normalized exports against committed files and exits non-zero on any staleness.

`preflight_runner.py` is the labeled-check runner consumer preflights thin into: `run_checks(checks)` executes a declarative list of `CommandCheck` (label + shell command under a `ci_step` group) and `GeneratedCheck` (label + generate command + pathspec + fix command — runs the generator, then fails on any `git status --porcelain` dirt under the paths, showing the diff and the fix command). Fail-fast; each check's duration lands in the Actions step summary via `ci_step`.

`sync_ruff.py` writes the org-canonical ruff config (`src/python_devkit/ruff.base.toml`, shipped as package data) into a consuming repo's root as `ruff.base.toml`; `--check` is the drift gate (byte compare against the packaged canonical). The verb also validates the consuming repo's `ruff.toml` layer: it must set `extend = "ruff.base.toml"` and use only extend keys — plain `exclude`/`lint.select`/`lint.ignore`/`lint.per-file-ignores` in the layer replace the canonical settings under `extend` and fail the check. This repo consumes its own canonical the same way: root `ruff.base.toml` is a verb-written copy of the packaged one, root `ruff.toml` is the (currently empty) local layer.

`.github/workflows/check.yml` is the org's reusable Python check workflow (`workflow_call`): checkout, cached `setup-uv`, ruff check + format, basedpyright, pytest behind a `test` input (default true), and the ruff drift gate. The drift gate's `python-devkit==0.1.3` uvx pin is internal to this one file — bumping it is a single workflow edit that reaches consumers as a workflow-SHA bump, not a per-repo edit wave. This repo's own `ci.yml` calls it via local path with `test: false` (no test suite yet); every other tool repo pins it cross-repo by pushed SHA. The workflow must stay self-contained: inline `astral-sh/setup-uv@v7`, no relative composite-action references (those resolve against the caller's checkout), no repo-specific values.

## Constraints

- **The module surface is cross-repo Python API.** `python_devkit.lock_python.lock_python(check, root)` and `python_devkit.preflight_runner.run_checks(checks)` are contract: placeframe's preflight calls both in-process, the lock-python entry point is on CI's path, and the `[tool.python-devkit.lock-python]` table in consumer root pyprojects is its declarative config surface.
- **The canonical ruff body is byte-stable contract.** Every consuming repo's `ruff.base.toml` is a verbatim copy compared byte-for-byte (after newline normalization); a cosmetic edit to the canonical ripples into every consumer's diff by design. Repo-local deltas never go here — they go in the consumer's `ruff.toml` extend layer. The canonical enables `strictly-empty-init-modules` (RUF067 strict): `__init__.py` files carry no code and no re-exports — consumers import submodule paths, and a package init that genuinely needs an import side effect carries a site-level `# ruff: noqa: RUF067 — <reason>` header (the bashrun-wrapper pattern, e.g. placeframe's zed-capture logging bootstrap).
- **`group-export-dirs` is devkit-owned and `extra="forbid"`.** A typo'd key in that table fails validation loudly rather than silently dropping the redirect (the failure mode is per-group pylocks appearing in member directories).
- **The redirect contract assumes identical group declarations.** Dedup is first-member-wins; members declaring the same redirected group differently get whichever member enumerates first, silently.
- **Export commands are byte-stability load-bearing.** The exact `uv export` flag order must not churn — committed pylocks are compared byte-for-byte (after newline normalization), so a cosmetic flag change ripples into every consumer's diff.
- **uv invocations run with `cwd=root`.** `--root` (default: current directory) exists so the verb and the library call work from anywhere; the uv commands themselves must execute inside the workspace root.

## Release flow

`release.yml` (workflow_run-gated on CI) publishes via release-devkit uvx-isolated under OIDC trusted publishing (publisher bound to `release.yml`, no environment); the first release is 0.1.0 on the fresh `python-devkit-v*` tag ledger. The committed `pyproject.toml` version is permanently the `0.0.0.dev0` sentinel; the tags are the version ledger. API-breaking changes ship with a manually bumped version — patch-auto assumes additive changes.

## See also

- `README.md` — human-facing overview.
- [tooling-consolidation.md](https://github.com/outernet-foundation/placeframe/blob/dev/design/tooling-consolidation.md) — the program this repo belongs to.
