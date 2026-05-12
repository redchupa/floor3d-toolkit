"""Smoke tests for the CLI entry point."""

from __future__ import annotations

from typer.testing import CliRunner

from floor3d_toolkit import __version__
from floor3d_toolkit.cli import app

runner = CliRunner()


def test_version_command_prints_package_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_help_lists_convert_and_inspect() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "convert" in result.stdout
    assert "inspect" in result.stdout


def test_convert_missing_input_errors_cleanly(tmp_path) -> None:
    bogus = tmp_path / "nope.sh3d"
    result = runner.invoke(app, ["convert", str(bogus)])
    assert result.exit_code != 0
