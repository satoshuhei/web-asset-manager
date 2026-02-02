from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from app import create_app


def _build_client_with_db(tmp_path: Path) -> tuple[TestClient, Path]:
    db_path = tmp_path / "test.sqlite3"
    app = create_app(str(db_path))
    return TestClient(app), db_path


def _build_client(tmp_path: Path) -> TestClient:
    client, _ = _build_client_with_db(tmp_path)
    return client


def _fetch_one(db_path: Path, query: str, params: tuple = ()) -> sqlite3.Row | None:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.execute(query, params)
    row = cur.fetchone()
    conn.close()
    return row


def test_assets_page_loads(tmp_path: Path) -> None:
    client = _build_client(tmp_path)
    response = client.get("/assets")
    assert response.status_code == 200
    assert "デバイス" in response.text


def test_create_device(tmp_path: Path) -> None:
    client = _build_client(tmp_path)
    response = client.post(
        "/assets/devices",
        data={
            "asset_no": "DEV-100",
            "display_name": "Test Device",
            "device_type": "PC",
            "model": "Model-X",
            "version": "2025",
            "state": "active",
            "note": "",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    page = client.get("/assets/devices")
    assert "DEV-100" in page.text


def test_create_license(tmp_path: Path) -> None:
    client = _build_client(tmp_path)
    response = client.post(
        "/assets/licenses",
        data={
            "license_no": "LIC-100",
            "name": "Test License",
            "license_key": "KEY-100",
            "state": "active",
            "note": "",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    page = client.get("/assets/licenses")
    assert "LIC-100" in page.text


def test_configurations_page_loads(tmp_path: Path) -> None:
    client = _build_client(tmp_path)
    response = client.get("/configurations")
    assert response.status_code == 200
    assert "構成を作成" in response.text


def test_configuration_detail(tmp_path: Path) -> None:
    client = _build_client(tmp_path)
    response = client.get("/configurations/1")
    assert response.status_code == 200
    assert "構成詳細" in response.text


def test_assign_device(tmp_path: Path) -> None:
    client = _build_client(tmp_path)
    response = client.post(
        "/api/configs/1/assign",
        json={"asset_type": "device", "asset_id": 1, "source_config_id": None},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_save_position(tmp_path: Path) -> None:
    client = _build_client(tmp_path)
    response = client.post(
        "/api/configs/1/position",
        json={"x": 120, "y": 240},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health(tmp_path: Path) -> None:
    client = _build_client(tmp_path)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_summary(tmp_path: Path) -> None:
    client = _build_client(tmp_path)
    response = client.get("/api/summary")
    assert response.status_code == 200
    payload = response.json()
    assert "devices" in payload
    assert "licenses" in payload
    assert "configs" in payload


def test_config_create_audit(tmp_path: Path) -> None:
    client, db_path = _build_client_with_db(tmp_path)
    response = client.post(
        "/configurations",
        data={"name": "監査テスト構成", "note": "audit"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    row = _fetch_one(
        db_path,
        "SELECT action, details_json FROM audit_logs WHERE action = 'config.create' ORDER BY audit_id DESC",
    )
    assert row is not None
    assert row["action"] == "config.create"
    assert "監査テスト構成" in row["details_json"]


def test_config_update_audit(tmp_path: Path) -> None:
    client, db_path = _build_client_with_db(tmp_path)
    response = client.post(
        "/configurations",
        data={"name": "更新前", "note": "note"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    config_row = _fetch_one(db_path, "SELECT config_id FROM configurations WHERE name = ?", ("更新前",))
    assert config_row is not None
    config_id = int(config_row["config_id"])
    response = client.post(
        f"/configurations/{config_id}/edit",
        data={"name": "更新後", "note": "note2"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    audit_row = _fetch_one(
        db_path,
        "SELECT action, details_json FROM audit_logs WHERE config_id = ? AND action = 'config.update' ORDER BY audit_id DESC",
        (config_id,),
    )
    assert audit_row is not None
    assert "更新前" in audit_row["details_json"]
    assert "更新後" in audit_row["details_json"]


def test_config_delete_audit(tmp_path: Path) -> None:
    client, db_path = _build_client_with_db(tmp_path)
    response = client.post(
        "/configurations",
        data={"name": "削除対象", "note": "note"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    config_row = _fetch_one(db_path, "SELECT config_id FROM configurations WHERE name = ?", ("削除対象",))
    assert config_row is not None
    config_id = int(config_row["config_id"])
    response = client.post(f"/configurations/{config_id}/delete", follow_redirects=False)
    assert response.status_code == 303
    audit_row = _fetch_one(
        db_path,
        "SELECT action FROM audit_logs WHERE config_id = ? AND action = 'config.delete' ORDER BY audit_id DESC",
        (config_id,),
    )
    assert audit_row is not None


def test_move_device_audit(tmp_path: Path) -> None:
    client, db_path = _build_client_with_db(tmp_path)
    response = client.post(
        "/api/configs/2/assign",
        json={"asset_type": "device", "asset_id": 1, "source_config_id": 1},
    )
    assert response.status_code == 200
    audit_row = _fetch_one(
        db_path,
        "SELECT action FROM audit_logs WHERE config_id = 2 AND action = 'config.device.move' ORDER BY audit_id DESC",
    )
    assert audit_row is not None
