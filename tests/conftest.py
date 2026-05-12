"""Shared pytest fixtures.

All fixtures here MUST be synthetic — never reference real floor plans.
See PLAN.md §7 (security guard).
"""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def sample_apartment_sh3d(fixtures_dir: Path) -> Path:
    """A synthetic 2-bedroom apartment .sh3d file used across tests.

    The fixture file itself is checked into ``tests/fixtures/`` as ``sample_apartment.sh3d``.
    Generation instructions: see ``tests/fixtures/README.md``.
    """
    path = fixtures_dir / "sample_apartment.sh3d"
    if not path.exists():
        pytest.skip(
            "sample_apartment.sh3d not present — generate per tests/fixtures/README.md "
            "(synthetic data only, NEVER real home plans)."
        )
    return path
