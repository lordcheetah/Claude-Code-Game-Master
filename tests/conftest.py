"""Shared pytest fixtures.

The DCC campaign under tests/fixtures/world-state is the read-only golden
fixture. Each test gets a throwaway copy in a tmp dir so the managers (which can
write) never touch the checked-in fixture or any live campaign.
"""

import shutil
from pathlib import Path

import pytest

FIXTURE_WORLD_STATE = Path(__file__).parent / "fixtures" / "world-state"


@pytest.fixture
def dcc_world(tmp_path):
    """Return a path to a hermetic, writable copy of the DCC world-state.

    Point managers at this via their `world_state_dir` arg. active-campaign.txt
    selects the dungeon-crawler-carl campaign inside it.
    """
    dest = tmp_path / "world-state"
    shutil.copytree(FIXTURE_WORLD_STATE, dest)
    return str(dest)
