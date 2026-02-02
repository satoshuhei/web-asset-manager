from __future__ import annotations

from pathlib import Path

from wam.db import init_db


def test_seed_data(tmp_path: Path) -> None:
    db_path = tmp_path / "seed.sqlite3"
    conn = init_db(str(db_path))
    device_count = conn.execute("SELECT COUNT(*) FROM devices").fetchone()[0]
    license_count = conn.execute("SELECT COUNT(*) FROM licenses").fetchone()[0]
    config_count = conn.execute("SELECT COUNT(*) FROM configurations").fetchone()[0]

    assert device_count > 0
    assert license_count > 0
    assert config_count > 0
