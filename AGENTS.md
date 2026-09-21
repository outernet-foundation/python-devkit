# python-devkit

## What this is

The python repo-lifecycle devkit — the `-devkit` family's home for tooling every Python repo needs at dev/CI time: the GitHub Actions step wrapper, CI runner provisioning, and (per the tooling-consolidation program) the generalized `lock-python`, the preflight check runner, the canonical ruff configuration with its sync verb and drift gate, and the reusable python check workflow. The org's one dedicated Python-domain devkit: runtime libraries stay standalone (`logger-conf`, `bashrun`), and registry-specific machinery lives in `release-devkit`.

The package is `python_devkit` (src-layout under `src/python_devkit/`); all dependencies resolve from PyPI (`bashrun`, `pydantic`, `pydantic-settings`; git-source pins only in scratch branches testing unreleased changes). Born 2026-09-21 from unity-devkit's `ci_step` + runner-setup cohort moving out (release-devkit's unity dependency dropped to zero in the same change).

## Release flow

Publishing rides `release.yml`, triggered by a successful CI run on a `main` push: the machinery — release-devkit, invoked uvx-isolated, never a project dependency — computes the plan from the tag ledger and path-diff, patches the version ephemerally, and publishes to PyPI under OIDC trusted publishing (publisher bound to `release.yml`, no environment). The committed `pyproject.toml` version is permanently the `0.0.0.dev0` sentinel; the `python-devkit-v*` tags are the version ledger (first release `0.1.0`, patch-auto thereafter). API-breaking changes ship with a manually bumped version — patch-auto assumes additive changes.

## Shape

| Module | Role |
|---|---|
| `ci_step.py` | `ci_step(label)` context manager — wraps a step in `::group::`/`::endgroup::`, times it, and appends a duration row to `$GITHUB_STEP_SUMMARY` (failure-marked on exception). |
| `setup.py` | CI runner provisioning: `configure_git` (re-sets checkout's `safe.directory` in the real HOME), `free_disk_space` (strips preinstalled toolchains; container/bare-linux/Windows paths), `install_dotnet` (via the vendored `third-party/dotnet-install.sh`, PATH + `$GITHUB_PATH` wiring), `install_node` (nodejs.org tarball, npm registry override). |
| `setup_oras.py` | `install_oras` — installs the ORAS CLI (zstd dependency included) and logs into ghcr.io with the job token. |
| `third-party/` | Vendored `dotnet-install.sh` (curl-downloading it inside CI containers is unreliable — the same reason `actions/setup-dotnet` bundles it); resolved `__file__`-relative, so it works in editable installs, wheels, and git checkouts alike. |

## Constraints

- **The module surface is cross-repo Python API.** `ci_step`, the `setup` functions, and `install_oras` are imported by release-devkit, unity-devkit, and consumer repos' CI commands — the import paths and signatures are contract, not internals. This package must stay dependency-light: anything with a heavyweight or domain-specific dep graph (Unity, docker, registry feeds) belongs in its sibling devkit, not here.
- **No Unity- or registry-specific code.** Unity build tooling lives in `unity-devkit`; compose-stack lifecycle in `docker-devkit`; publication machinery in `release-devkit`. When a module grows a domain, it moves out — this repo is the domainless floor.
- **CI tooling prints to stdout by design** — step output is the operator interface; the `print` ignore rides the org-wide PLE-336 deferral like the sibling devkits and will never convert to structured logging here.

## See also

- `README.md` — human-facing setup and consumer install snippet.
- [`bashrun`](https://github.com/outernet-foundation/bashrun) — the shell-exec helpers the provisioning functions use.
