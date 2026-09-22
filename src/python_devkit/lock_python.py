from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path
from tomllib import load
from typing import Annotated, Any

import typer
from bashrun.bash import bash, bash_check, bash_output
from pydantic import BaseModel, ConfigDict, Field

app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)


class LockPythonConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    group_export_dirs: dict[str, Path] = Field(default_factory=dict, alias="group-export-dirs")


class WorkspaceConfig(BaseModel):
    members: list[str] = Field(default_factory=list)


class ProjectConfig(BaseModel):
    name: str


class PackageConfig(BaseModel):
    project: ProjectConfig
    dependency_groups: dict[str, Any] = Field(default_factory=dict, alias="dependency-groups")


@app.command()
def lock_python(
    check: Annotated[
        bool, typer.Option("--check", help="Validate lock files without writing; exit non-zero if stale.")
    ] = False,
    root: Annotated[Path, typer.Option(help="uv workspace root; defaults to the current directory.")] = Path(),
) -> None:
    root = root.resolve()
    stale = False

    if check:
        print("Checking uv.lock...")
        if not bash_check("uv lock --check", cwd=root):
            print("  STALE: uv.lock is out of date. Run 'uv run lock-python' to update.")
            stale = True
        else:
            print("  OK")
    else:
        bash("uv lock", cwd=root)

    with (root / "pyproject.toml").open("rb") as file:
        workspace_toml = load(file)

    tool = workspace_toml.get("tool", {})
    workspace = WorkspaceConfig.model_validate(tool.get("uv", {}).get("workspace", {}))
    config = LockPythonConfig.model_validate(tool.get("python-devkit", {}).get("lock-python", {}))

    seen_redirected: set[str] = set()

    for member in workspace.members:
        member_dir = root / member

        if not (member_dir / "Dockerfile").exists():
            continue

        with (member_dir / "pyproject.toml").open("rb") as file:
            package = PackageConfig.model_validate(load(file))

        stale |= _export_pylock(check, root, member_dir, package.project.name, group=None)

        for group in package.dependency_groups:
            if group == "dev":
                continue
            redirect = _redirect_dir(group, config, root)
            if redirect is None:
                stale |= _export_pylock(check, root, member_dir, package.project.name, group=group)
                continue
            if group in seen_redirected:
                continue
            seen_redirected.add(group)
            stale |= _export_pylock(check, root, redirect, package.project.name, group=group)

    if check and stale:
        raise SystemExit(1)

    if check:
        print("\nAll Python lock files are up to date.")


def _export_pylock(check: bool, root: Path, export_dir: Path, package_name: str, group: str | None) -> bool:
    if group:
        pylock = export_dir / f"pylock.{group}.toml"
        group_flags = f"--only-group {group} "
    else:
        pylock = export_dir / "pylock.toml"
        group_flags = "--no-default-groups "

    export_command = (
        f"uv export --format pylock.toml --no-header --package {package_name} {group_flags}--no-emit-local --frozen "
    )

    if check:
        print(f"Checking {pylock}...")
        exported = _normalize_line_endings(bash_output(export_command, cwd=root))
        committed = _normalize_line_endings(pylock.read_text(encoding="utf-8")) if pylock.exists() else ""
        if exported != committed:
            print(f"  STALE: {pylock} is out of date.")
            return True
        print("  OK")
        return False

    bash(export_command + f"--output-file {pylock} ", cwd=root)
    text = pylock.read_text(encoding="utf-8")
    with pylock.open("w", encoding="utf-8", newline="\n") as file:
        file.write(text)
    return False


def _normalize_line_endings(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _redirect_dir(group: str, config: LockPythonConfig, root: Path) -> Path | None:
    for pattern, directory in config.group_export_dirs.items():
        if fnmatch(group, pattern):
            return root / directory
    return None
