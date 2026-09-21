from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from bashrun import bash, bash_output
from ci_devkit.ci_step import ci_step
from pydantic import BaseModel


class CommandCheck(BaseModel):
    label: str
    command: str


class GeneratedCheck(BaseModel):
    label: str
    generate_command: str
    paths: list[Path]
    fix_command: str


def run_checks(checks: Sequence[CommandCheck | GeneratedCheck], *, cwd: Path | None = None) -> None:
    for check in checks:
        if isinstance(check, CommandCheck):
            _run_command_check(check, cwd)
        else:
            _run_generated_check(check, cwd)


def _run_command_check(check: CommandCheck, cwd: Path | None) -> None:
    with ci_step(check.label):
        bash(check.command, cwd=cwd)


def _run_generated_check(check: GeneratedCheck, cwd: Path | None) -> None:
    with ci_step(check.label):
        bash(check.generate_command, cwd=cwd)
        pathspec = " ".join(str(path) for path in check.paths)
        staleness_output = bash_output(f"git status --porcelain -- {pathspec}", cwd=cwd)
        if staleness_output.strip():
            bash(f"git diff -- {pathspec}", cwd=cwd)
            raise SystemExit(f"{check.label} output is stale. Run '{check.fix_command}' locally and commit the result.")
