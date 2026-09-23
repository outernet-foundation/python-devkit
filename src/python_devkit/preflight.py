from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path
from tomllib import load
from typing import Annotated

import typer
from bashrun.bash import bash
from ci_devkit.ci_step import ci_step
from pydantic import BaseModel, ConfigDict, Field

from .lock_python import lock_python
from .sync_ruff import sync_ruff

app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)

DEPTRY_VERSION = "0.24.0"


class PreflightConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tests: bool = True
    sync_args: list[str] = Field(default_factory=list, alias="sync-args")
    deptry_exclude: list[str] = Field(default_factory=list, alias="deptry-exclude")


class WorkspaceConfig(BaseModel):
    members: list[str] = Field(default_factory=list)


@app.command()
def preflight(
    root: Annotated[Path, typer.Option(help="Repository root; defaults to the current directory.")] = Path(),
) -> None:
    root = root.resolve()
    with (root / "pyproject.toml").open("rb") as file:
        tool = load(file).get("tool", {})

    config = PreflightConfig.model_validate(tool.get("python-devkit", {}).get("preflight", {}))
    members = WorkspaceConfig.model_validate(tool.get("uv", {}).get("workspace", {})).members

    with ci_step("Sync"):
        bash(f"uv sync {' '.join(config.sync_args)}".rstrip(), cwd=root)

    with ci_step("Lint"):
        bash("uv run ruff check .", cwd=root)

    with ci_step("Format"):
        bash("uv run ruff format --check .", cwd=root)

    with ci_step("Type check"):
        bash("uv run basedpyright", cwd=root)

    with ci_step("Dependency check"):
        if not members:
            targets = ["."]
        else:
            targets: list[str] = []
            for member in members:
                if any(fnmatch(member, pattern) for pattern in config.deptry_exclude):
                    continue
                if not (root / member / "pyproject.toml").exists():
                    continue
                targets.append(member)
        for target in targets:
            bash(f"uv run --no-sync --with deptry=={DEPTRY_VERSION} deptry .", cwd=root / target)

    with ci_step("Check lock files"):
        lock_python(check=True, root=root)

    with ci_step("Check ruff config"):
        sync_ruff(check=True, root=root)

    if config.tests:
        with ci_step("Test"):
            bash("uv run pytest", cwd=root)
