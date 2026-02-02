from __future__ import annotations

import sqlite3


def init_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS devices (
            device_id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_no TEXT UNIQUE NOT NULL,
            display_name TEXT,
            device_type TEXT NOT NULL,
            model TEXT NOT NULL,
            version TEXT NOT NULL,
            state TEXT NOT NULL,
            note TEXT NOT NULL DEFAULT ''
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS licenses (
            license_id INTEGER PRIMARY KEY AUTOINCREMENT,
            license_no TEXT NOT NULL,
            name TEXT NOT NULL,
            license_key TEXT NOT NULL,
            state TEXT NOT NULL,
            note TEXT NOT NULL DEFAULT ''
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS configurations (
            config_id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_no TEXT,
            name TEXT NOT NULL,
            note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS config_devices (
            config_id INTEGER NOT NULL,
            device_id INTEGER NOT NULL,
            PRIMARY KEY (config_id, device_id),
            FOREIGN KEY (config_id) REFERENCES configurations(config_id)
                ON DELETE CASCADE,
            FOREIGN KEY (device_id) REFERENCES devices(device_id)
                ON DELETE CASCADE
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS config_licenses (
            config_id INTEGER NOT NULL,
            license_id INTEGER NOT NULL UNIQUE,
            note TEXT NOT NULL DEFAULT '',
            PRIMARY KEY (config_id, license_id),
            FOREIGN KEY (config_id) REFERENCES configurations(config_id)
                ON DELETE CASCADE,
            FOREIGN KEY (license_id) REFERENCES licenses(license_id)
                ON DELETE CASCADE
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS config_positions (
            config_id INTEGER PRIMARY KEY,
            x REAL NOT NULL,
            y REAL NOT NULL,
            hidden INTEGER NOT NULL DEFAULT 0
        )
        """
    )

    _ensure_config_no(conn)
    _ensure_license_no(conn)
    _seed_sample_data(conn)
    conn.commit()
    return conn


def _ensure_config_no(conn: sqlite3.Connection) -> None:
    columns = [row[1] for row in conn.execute("PRAGMA table_info(configurations)")]
    if "config_no" not in columns:
        conn.execute("ALTER TABLE configurations ADD COLUMN config_no TEXT")
    conn.execute(
        """
        UPDATE configurations
        SET config_no = printf('CNFG-%03d', config_id)
        WHERE config_no IS NULL OR config_no = ''
        """
    )


def _ensure_license_no(conn: sqlite3.Connection) -> None:
    columns = [row[1] for row in conn.execute("PRAGMA table_info(licenses)")]
    if "license_no" not in columns:
        conn.execute("ALTER TABLE licenses ADD COLUMN license_no TEXT")
    conn.execute(
        """
        UPDATE licenses
        SET license_no = printf('LIC-%03d', license_id)
        WHERE license_no IS NULL OR license_no = ''
        """
    )


def _seed_sample_data(conn: sqlite3.Connection) -> None:
    device_count = conn.execute("SELECT COUNT(*) FROM devices").fetchone()[0]
    if device_count == 0:
        conn.executemany(
            """
            INSERT INTO devices (asset_no, display_name, device_type, model, version, state, note)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("DEV-001", "解析ワークステーション", "PC", "Precision 3660", "2024", "active", "sample"),
                ("DEV-002", "ログ収集ノート", "Laptop", "ThinkPad P1", "Gen 6", "active", "sample"),
                ("DEV-003", "CANインターフェース", "Interface", "Vector VN1610", "v2", "active", "sample"),
                ("DEV-004", "J2534パススルー", "Interface", "MongoosePro", "v3", "active", "sample"),
            ],
        )

    license_count = conn.execute("SELECT COUNT(*) FROM licenses").fetchone()[0]
    if license_count == 0:
        conn.executemany(
            """
            INSERT INTO licenses (license_no, name, license_key, state, note)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                ("LIC-001", "CANape", "CANAPE-SAMPLE-001", "active", "sample"),
                ("LIC-002", "CANalyzer", "CANA-SAMPLE-002", "active", "sample"),
                ("LIC-003", "CANoe", "CANOE-SAMPLE-003", "active", "sample"),
            ],
        )

    config_count = conn.execute("SELECT COUNT(*) FROM configurations").fetchone()[0]
    if config_count == 0:
        conn.executemany(
            """
            INSERT INTO configurations (config_no, name, note)
            VALUES (?, ?, ?)
            """,
            [
                ("CNFG-001", "ECU解析-エンジン", "sample"),
                ("CNFG-002", "ECU解析-ADAS", "sample"),
                ("CNFG-003", "ECU解析-ボディ", "sample"),
            ],
        )

    config_device_count = conn.execute("SELECT COUNT(*) FROM config_devices").fetchone()[0]
    config_license_count = conn.execute("SELECT COUNT(*) FROM config_licenses").fetchone()[0]
    if config_device_count == 0 and config_license_count == 0:
        config_ids = [row[0] for row in conn.execute("SELECT config_id FROM configurations ORDER BY config_id")]
        device_ids = [row[0] for row in conn.execute("SELECT device_id FROM devices ORDER BY device_id")]
        license_ids = [row[0] for row in conn.execute("SELECT license_id FROM licenses ORDER BY license_id")]

        for index, config_id in enumerate(config_ids):
            if index < len(device_ids):
                conn.execute(
                    """
                    INSERT OR IGNORE INTO config_devices (config_id, device_id)
                    VALUES (?, ?)
                    """,
                    (config_id, device_ids[index]),
                )
            if license_ids:
                conn.execute(
                    """
                    INSERT INTO config_licenses (config_id, license_id, note)
                    VALUES (?, ?, ?)
                    ON CONFLICT(license_id) DO UPDATE SET config_id = excluded.config_id
                    """,
                    (config_id, license_ids[index % len(license_ids)], "sample"),
                )
