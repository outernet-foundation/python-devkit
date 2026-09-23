from pathlib import Path

import pytest
from pydantic import ValidationError

from python_devkit.preflight import DEPTRY_VERSION, PreflightConfig, preflight


def test_config_defaults() -> None:
    config = PreflightConfig.model_validate({})

    assert config.tests is True
    assert config.sync_args == []
    assert config.deptry_exclude == []


def test_config_aliases() -> None:
    config = PreflightConfig.model_validate({
        "tests": False,
        "sync-args": ["--all-packages", "--extra", "cpu"],
        "deptry-exclude": ["packages/generated/*"],
    })

    assert config.tests is False
    assert config.sync_args == ["--all-packages", "--extra", "cpu"]
    assert config.deptry_exclude == ["packages/generated/*"]


def test_config_forbids_unknown_keys() -> None:
    with pytest.raises(ValidationError):
        PreflightConfig.model_validate({"checks": []})


class BashRecorder:
    def __init__(self) -> None:
        self.commands: list[tuple[str, Path | None]] = []

    def __call__(self, command: str, *, cwd: Path | None = None) -> None:
        self.commands.append((command, cwd))


def fake_verb(*_args: object, **_kwargs: object) -> None:
    pass


def run_preflight(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pyproject: str) -> BashRecorder:
    (tmp_path / "pyproject.toml").write_text(pyproject, encoding="utf-8")
    recorder = BashRecorder()
    monkeypatch.setattr("python_devkit.preflight.bash", recorder)
    monkeypatch.setattr("python_devkit.preflight.lock_python", fake_verb)
    monkeypatch.setattr("python_devkit.preflight.sync_ruff", fake_verb)
    preflight(root=tmp_path)
    return recorder


def deptry_commands(recorder: BashRecorder) -> list[Path | None]:
    return [cwd for command, cwd in recorder.commands if command.endswith("deptry .")]


def test_deptry_runs_at_repo_root_for_plain_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    commands = run_preflight(tmp_path, monkeypatch, "[tool.python-devkit.preflight]\ntests = false\n")

    assert deptry_commands(commands) == [tmp_path.resolve()]


def test_deptry_targets_workspace_members_with_excludes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    core = tmp_path / "packages" / "core"
    core.mkdir(parents=True)
    (core / "pyproject.toml").write_text("", encoding="utf-8")
    generated_client = tmp_path / "packages" / "generated" / "client"
    generated_client.mkdir(parents=True)
    (generated_client / "pyproject.toml").write_text("", encoding="utf-8")

    pyproject = """\
[tool.uv.workspace]
members = ["packages/core", "packages/generated/client", "packages/missing"]

[tool.python-devkit.preflight]
tests = false
deptry-exclude = ["packages/generated/*"]
"""
    commands = run_preflight(tmp_path, monkeypatch, pyproject)

    assert deptry_commands(commands) == [(tmp_path / "packages" / "core").resolve()]
    assert all(
        f"deptry=={DEPTRY_VERSION}" in command for command, _cwd in commands.commands if command.endswith("deptry .")
    )
