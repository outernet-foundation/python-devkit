# python-devkit

The python repo-lifecycle devkit — workspace locking (`lock-python`), the preflight check runner, and the canonical ruff configuration with its sync verb and drift gate, per the tooling-consolidation program. Purely python-domain by charter: the CI runner floor (step wrapper, runner provisioning, git tags, OCI cache) lives in [`ci-devkit`](https://github.com/outernet-foundation/ci-devkit), which this package will depend on.

The package is empty of content until its first module lands — it does not publish until then. Runtime dependencies arrive with the modules that need them.

## Release flow

`release.yml` (workflow_run-gated on CI) publishes via release-devkit uvx-isolated under OIDC trusted publishing (publisher bound to `release.yml`, no environment), once the package carries content. The committed `pyproject.toml` version is permanently the `0.0.0.dev0` sentinel; the `python-devkit-v*` tags will be the version ledger. API-breaking changes ship with a manually bumped version — patch-auto assumes additive changes.

## See also

- `README.md` — human-facing overview.
- [tooling-consolidation.md](https://github.com/outernet-foundation/placeframe/blob/dev/design/tooling-consolidation.md) — the program this repo belongs to.
