from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from wam.models import Configuration, Device, License


class DeviceRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def create(
        self,
        asset_no: str,
        display_name: Optional[str],
        device_type: str,
        model: str,
        version: str,
        state: str,
        note: str,
    ) -> Device:
        cur = self._conn.execute(
            """
            INSERT INTO devices (asset_no, display_name, device_type, model, version, state, note)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (asset_no, display_name, device_type, model, version, state, note),
        )
        self._conn.commit()
        return self.get_by_id(int(cur.lastrowid))

    def list_all(self) -> List[Device]:
        cur = self._conn.execute(
            """
            SELECT device_id, asset_no, display_name, device_type, model, version, state, note
            FROM devices
            ORDER BY device_id DESC
            """
        )
        return [Device(*row) for row in cur.fetchall()]

    def get_by_id(self, device_id: int) -> Device:
        cur = self._conn.execute(
            """
            SELECT device_id, asset_no, display_name, device_type, model, version, state, note
            FROM devices
            WHERE device_id = ?
            """,
            (device_id,),
        )
        row = cur.fetchone()
        if row is None:
            raise ValueError("Device not found")
        return Device(*row)

    def update(
        self,
        device_id: int,
        asset_no: str,
        display_name: Optional[str],
        device_type: str,
        model: str,
        version: str,
        state: str,
        note: str,
    ) -> Device:
        self._conn.execute(
            """
            UPDATE devices
            SET asset_no = ?, display_name = ?, device_type = ?, model = ?, version = ?, state = ?, note = ?
            WHERE device_id = ?
            """,
            (asset_no, display_name, device_type, model, version, state, note, device_id),
        )
        self._conn.commit()
        return self.get_by_id(device_id)

    def delete(self, device_id: int) -> None:
        self._conn.execute("DELETE FROM devices WHERE device_id = ?", (device_id,))
        self._conn.commit()


class LicenseRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def create(self, license_no: str, name: str, license_key: str, state: str, note: str) -> License:
        cur = self._conn.execute(
            """
            INSERT INTO licenses (license_no, name, license_key, state, note)
            VALUES (?, ?, ?, ?, ?)
            """,
            (license_no, name, license_key, state, note),
        )
        self._conn.commit()
        return self.get_by_id(int(cur.lastrowid))

    def list_all(self) -> List[License]:
        cur = self._conn.execute(
            """
            SELECT license_id, license_no, name, license_key, state, note
            FROM licenses
            ORDER BY license_id DESC
            """
        )
        return [License(*row) for row in cur.fetchall()]

    def get_by_id(self, license_id: int) -> License:
        cur = self._conn.execute(
            """
            SELECT license_id, license_no, name, license_key, state, note
            FROM licenses
            WHERE license_id = ?
            """,
            (license_id,),
        )
        row = cur.fetchone()
        if row is None:
            raise ValueError("License not found")
        return License(*row)

    def update(
        self,
        license_id: int,
        license_no: str,
        name: str,
        license_key: str,
        state: str,
        note: str,
    ) -> License:
        self._conn.execute(
            """
            UPDATE licenses
            SET license_no = ?, name = ?, license_key = ?, state = ?, note = ?
            WHERE license_id = ?
            """,
            (license_no, name, license_key, state, note, license_id),
        )
        self._conn.commit()
        return self.get_by_id(license_id)

    def delete(self, license_id: int) -> None:
        self._conn.execute("DELETE FROM licenses WHERE license_id = ?", (license_id,))
        self._conn.commit()


class ConfigRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def create(self, name: str, note: str, config_no: Optional[str] = None) -> Configuration:
        if config_no is None:
            next_id = self._conn.execute("SELECT COALESCE(MAX(config_id), 0) + 1 FROM configurations").fetchone()[0]
            config_no = f"CNFG-{int(next_id):03d}"
        cur = self._conn.execute(
            """
            INSERT INTO configurations (config_no, name, note)
            VALUES (?, ?, ?)
            """,
            (config_no, name, note),
        )
        self._conn.commit()
        return self.get_by_id(int(cur.lastrowid))

    def list_all(self) -> List[Configuration]:
        cur = self._conn.execute(
            """
            SELECT config_id, config_no, name, note, created_at, updated_at
            FROM configurations
            ORDER BY config_id ASC
            """
        )
        return [Configuration(*row) for row in cur.fetchall()]

    def get_by_id(self, config_id: int) -> Configuration:
        cur = self._conn.execute(
            """
            SELECT config_id, config_no, name, note, created_at, updated_at
            FROM configurations
            WHERE config_id = ?
            """,
            (config_id,),
        )
        row = cur.fetchone()
        if row is None:
            raise ValueError("Configuration not found")
        return Configuration(*row)

    def update(self, config_id: int, name: str, note: str) -> Configuration:
        self._conn.execute(
            """
            UPDATE configurations
            SET name = ?, note = ?, updated_at = CURRENT_TIMESTAMP
            WHERE config_id = ?
            """,
            (name, note, config_id),
        )
        self._conn.commit()
        return self.get_by_id(config_id)

    def delete(self, config_id: int) -> None:
        self._conn.execute("DELETE FROM configurations WHERE config_id = ?", (config_id,))
        self._conn.commit()

    def list_devices(self, config_id: int) -> List[Device]:
        cur = self._conn.execute(
            """
            SELECT d.device_id, d.asset_no, d.display_name, d.device_type, d.model, d.version, d.state, d.note
            FROM devices d
            INNER JOIN config_devices cd ON cd.device_id = d.device_id
            WHERE cd.config_id = ?
            ORDER BY d.device_id DESC
            """,
            (config_id,),
        )
        return [Device(*row) for row in cur.fetchall()]

    def list_licenses(self, config_id: int) -> List[License]:
        cur = self._conn.execute(
            """
            SELECT l.license_id, l.license_no, l.name, l.license_key, l.state, l.note
            FROM licenses l
            INNER JOIN config_licenses cl ON cl.license_id = l.license_id
            WHERE cl.config_id = ?
            ORDER BY l.license_id DESC
            """,
            (config_id,),
        )
        return [License(*row) for row in cur.fetchall()]

    def list_assigned_device_ids(self) -> List[int]:
        cur = self._conn.execute("SELECT DISTINCT device_id FROM config_devices")
        return [row[0] for row in cur.fetchall()]

    def list_assigned_license_ids(self) -> List[int]:
        cur = self._conn.execute("SELECT DISTINCT license_id FROM config_licenses")
        return [row[0] for row in cur.fetchall()]

    def get_device_owner(self, device_id: int) -> Optional[int]:
        cur = self._conn.execute(
            """
            SELECT config_id
            FROM config_devices
            WHERE device_id = ?
            """,
            (device_id,),
        )
        row = cur.fetchone()
        return int(row[0]) if row else None

    def get_license_owner(self, license_id: int) -> Optional[int]:
        cur = self._conn.execute(
            """
            SELECT config_id
            FROM config_licenses
            WHERE license_id = ?
            """,
            (license_id,),
        )
        row = cur.fetchone()
        return int(row[0]) if row else None

    def assign_device(self, config_id: int, device_id: int) -> None:
        owner = self.get_device_owner(device_id)
        if owner is not None and owner != config_id:
            raise ValueError("Device already assigned")
        self._conn.execute(
            """
            INSERT OR IGNORE INTO config_devices (config_id, device_id)
            VALUES (?, ?)
            """,
            (config_id, device_id),
        )
        self._touch_config(config_id)
        self._conn.commit()

    def move_device(self, from_config_id: int, to_config_id: int, device_id: int) -> None:
        if from_config_id == to_config_id:
            return
        self.unassign_device(from_config_id, device_id)
        self.assign_device(to_config_id, device_id)

    def unassign_device(self, config_id: int, device_id: int) -> None:
        self._conn.execute(
            """
            DELETE FROM config_devices
            WHERE config_id = ? AND device_id = ?
            """,
            (config_id, device_id),
        )
        self._touch_config(config_id)
        self._conn.commit()

    def assign_license(self, config_id: int, license_id: int, note: str = "") -> None:
        owner = self.get_license_owner(license_id)
        if owner is not None and owner != config_id:
            raise ValueError("License already assigned")
        if owner == config_id:
            self._conn.execute(
                """
                UPDATE config_licenses
                SET note = ?
                WHERE config_id = ? AND license_id = ?
                """,
                (note, config_id, license_id),
            )
        else:
            self._conn.execute(
                """
                INSERT INTO config_licenses (config_id, license_id, note)
                VALUES (?, ?, ?)
                """,
                (config_id, license_id, note),
            )
        self._touch_config(config_id)
        self._conn.commit()

    def unassign_license(self, config_id: int, license_id: int) -> None:
        self._conn.execute(
            """
            DELETE FROM config_licenses
            WHERE config_id = ? AND license_id = ?
            """,
            (config_id, license_id),
        )
        self._touch_config(config_id)
        self._conn.commit()

    def _touch_config(self, config_id: int) -> None:
        self._conn.execute(
            """
            UPDATE configurations
            SET updated_at = CURRENT_TIMESTAMP
            WHERE config_id = ?
            """,
            (config_id,),
        )


class PositionRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def load_positions(self) -> Dict[int, Tuple[float, float, bool]]:
        cur = self._conn.execute("SELECT config_id, x, y, hidden FROM config_positions")
        return {int(row[0]): (float(row[1]), float(row[2]), bool(row[3])) for row in cur.fetchall()}

    def save_position(self, config_id: int, x: float, y: float) -> None:
        self._conn.execute(
            """
            INSERT INTO config_positions (config_id, x, y, hidden)
            VALUES (?, ?, ?, COALESCE((SELECT hidden FROM config_positions WHERE config_id = ?), 0))
            ON CONFLICT(config_id) DO UPDATE SET x = excluded.x, y = excluded.y
            """,
            (config_id, x, y, config_id),
        )
        self._conn.commit()


@dataclass(frozen=True)
class AuditLog:
    audit_id: int
    config_id: int
    action: str
    actor: str
    details_json: str
    created_at: str
    prev_hash: Optional[str]
    entry_hash: str


class AuditRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def _get_last_hash(self, config_id: int) -> Optional[str]:
        cur = self._conn.execute(
            """
            SELECT entry_hash
            FROM audit_logs
            WHERE config_id = ?
            ORDER BY audit_id DESC
            LIMIT 1
            """,
            (config_id,),
        )
        row = cur.fetchone()
        return str(row[0]) if row else None

    @staticmethod
    def _compute_hash(
        created_at: str,
        config_id: int,
        action: str,
        actor: str,
        details_json: str,
        prev_hash: Optional[str],
    ) -> str:
        payload = "|".join(
            [
                created_at,
                str(config_id),
                action,
                actor,
                details_json,
                prev_hash or "",
            ]
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def append(
        self,
        *,
        config_id: int,
        action: str,
        actor: str,
        details: Dict[str, object],
        created_at: str,
    ) -> None:
        details_json = json.dumps(details, ensure_ascii=False, sort_keys=True)
        prev_hash = self._get_last_hash(config_id)
        entry_hash = self._compute_hash(created_at, config_id, action, actor, details_json, prev_hash)
        self._conn.execute(
            """
            INSERT INTO audit_logs (config_id, action, actor, details_json, created_at, prev_hash, entry_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (config_id, action, actor, details_json, created_at, prev_hash, entry_hash),
        )
        self._conn.commit()

    def list_by_config(self, config_id: int, limit: int = 100) -> List[AuditLog]:
        cur = self._conn.execute(
            """
            SELECT audit_id, config_id, action, actor, details_json, created_at, prev_hash, entry_hash
            FROM audit_logs
            WHERE config_id = ?
            ORDER BY audit_id DESC
            LIMIT ?
            """,
            (config_id, limit),
        )
        return [AuditLog(*row) for row in cur.fetchall()]
