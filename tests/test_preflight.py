from pathlib import Path

import pytest
from pydantic import ValidationError

from python_devkit.preflight import PreflightConfig, deptry_targets


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


def test_deptry_targets_plain_repo(tmp_path: Path) -> None:
    assert deptry_targets([], tmp_path, []) == ["."]


def test_deptry_targets_workspace_filters(tmp_path: Path) -> None:
    core = tmp_path / "packages" / "core"
    core.mkdir(parents=True)
    (core / "pyproject.toml").write_text("", encoding="utf-8")
    generated_client = tmp_path / "packages" / "generated" / "client"
    generated_client.mkdir(parents=True)
    (generated_client / "pyproject.toml").write_text("", encoding="utf-8")

    targets = deptry_targets(
        ["packages/core", "packages/generated/client", "packages/missing"], tmp_path, ["packages/generated/*"]
    )

    assert targets == ["packages/core"]
