from __future__ import annotations

from pathlib import Path

from wam.repositories import AuditRepository

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


def test_audit_hash_chain(tmp_path: Path) -> None:
    db_path = tmp_path / "audit.sqlite3"
    conn = init_db(str(db_path))
    repo = AuditRepository(conn)

    repo.append(
        config_id=1,
        action="config.create",
        actor="tester",
        details={"name": "hash-1"},
        created_at="2026-02-02T00:00:00+00:00",
    )
    repo.append(
        config_id=1,
        action="config.update",
        actor="tester",
        details={"name": "hash-2"},
        created_at="2026-02-02T00:01:00+00:00",
    )

    rows = conn.execute(
        "SELECT prev_hash, entry_hash FROM audit_logs WHERE config_id = 1 ORDER BY audit_id ASC"
    ).fetchall()
    assert rows[0][0] is None
    assert rows[1][0] == rows[0][1]
