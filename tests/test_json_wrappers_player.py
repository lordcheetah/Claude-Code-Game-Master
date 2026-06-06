"""Tests for json-wrappers-player: --json envelope over get (read) + hp (write)."""

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _run(dcc_world, *args):
    return subprocess.run(
        [sys.executable, str(ROOT / "lib" / "player_manager.py"), *args],
        capture_output=True, text=True, cwd=str(Path(dcc_world).parent), env={**os.environ},
    )


def test_get_json_envelope(dcc_world):
    r = _run(dcc_world, "get", "Tandy", "--json")
    assert r.returncode == 0, r.stderr
    d = json.loads(r.stdout)
    assert d["ok"] is True and d["data"].get("name") == "Tandy"


def test_hp_write_json_envelope(dcc_world):
    r = _run(dcc_world, "hp", "Tandy", "-5", "--json")
    assert r.returncode == 0, r.stderr
    d = json.loads(r.stdout)
    assert d["ok"] is True and d["data"].get("success") is True
