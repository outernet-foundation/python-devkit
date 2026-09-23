from __future__ import annotations

from pathlib import Path
from tomllib import load
from typing import Annotated

import typer
from pydantic import BaseModel, ConfigDict, Field

from .text import normalize_line_endings

app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)

CANONICAL_PATH = Path(__file__).parent / "ruff.base.toml"


class LayerLintConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    select: list[str] | None = None
    ignore: list[str] | None = None
    per_file_ignores: dict[str, list[str]] | None = Field(default=None, alias="per-file-ignores")


class LayerConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    extend: str | None = None
    exclude: list[str] | None = None
    lint: LayerLintConfig | None = None


@app.command()
def sync_ruff(
    check: Annotated[
        bool, typer.Option("--check", help="Validate ruff.base.toml without writing; exit non-zero if stale.")
    ] = False,
    root: Annotated[Path, typer.Option(help="Repository root; defaults to the current directory.")] = Path(),
) -> None:
    root = root.resolve()
    base_path = root / "ruff.base.toml"
    canonical = CANONICAL_PATH.read_text(encoding="utf-8")

    if check:
        print("Checking ruff.base.toml...")
        committed = base_path.read_text(encoding="utf-8") if base_path.exists() else ""
        if normalize_line_endings(committed) != normalize_line_endings(canonical):
            print("  STALE: ruff.base.toml diverges from python-devkit's canonical config.")
            print("  Run 'uvx --from python-devkit sync-ruff' to update.")
            raise SystemExit(1)
        print("  OK")
    else:
        with base_path.open("w", encoding="utf-8", newline="\n") as file:
            file.write(canonical)
        print(f"Wrote {base_path}")

    layer_path = root / "ruff.toml"
    if not layer_path.exists():
        print(f"BROKEN: {layer_path} is missing; the synced base needs an extending ruff.toml beside it.")
        raise SystemExit(1)

    with layer_path.open("rb") as file:
        layer = LayerConfig.model_validate(load(file))

    if layer.extend != "ruff.base.toml":
        print('BROKEN: ruff.toml must set extend = "ruff.base.toml".')
        raise SystemExit(1)

    offenders: list[str] = []
    if layer.exclude is not None:
        offenders.append("exclude -> extend-exclude")
    if layer.lint is not None:
        if layer.lint.select is not None:
            offenders.append("lint.select -> lint.extend-select")
        if layer.lint.ignore is not None:
            offenders.append("lint.ignore -> lint.extend-ignore")
        if layer.lint.per_file_ignores is not None:
            offenders.append("lint.per-file-ignores -> lint.extend-per-file-ignores")

    if offenders:
        print("BROKEN: plain keys replace the canonical settings under extend; use their extend-* forms:")
        for offender in offenders:
            print(f"  {offender}")
        raise SystemExit(1)
