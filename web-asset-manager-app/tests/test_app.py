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


def test_create_device_missing_required(tmp_path: Path) -> None:
    client = _build_client(tmp_path)
    response = client.post(
        "/assets/devices",
        data={
            "display_name": "Missing Asset No",
            "device_type": "PC",
            "model": "Model-X",
            "version": "2025",
            "state": "active",
            "note": "",
        },
    )
    assert response.status_code == 422


def test_create_device_asset_no_boundaries(tmp_path: Path) -> None:
    client = _build_client(tmp_path)
    response = client.post(
        "/assets/devices",
        data={
            "asset_no": "D",
            "display_name": "Min",
            "device_type": "PC",
            "model": "Model-Min",
            "version": "2025",
            "state": "active",
            "note": "",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    long_asset_no = "D" * 255
    response = client.post(
        "/assets/devices",
        data={
            "asset_no": long_asset_no,
            "display_name": "Max",
            "device_type": "PC",
            "model": "Model-Max",
            "version": "2025",
            "state": "active",
            "note": "",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    page = client.get("/assets/devices")
    assert "D" in page.text
    assert long_asset_no in page.text


def test_create_device_character_types(tmp_path: Path) -> None:
    client = _build_client(tmp_path)
    response = client.post(
        "/assets/devices",
        data={
            "asset_no": "DEV-ZENKAKU",
            "display_name": "テスト１２３",
            "device_type": "PC",
            "model": "Model-!@#",
            "version": "２０２６",
            "state": "active",
            "note": "記号!@#",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    page = client.get("/assets/devices")
    assert "DEV-ZENKAKU" in page.text
    assert "テスト１２３" in page.text


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


def test_create_license_missing_required(tmp_path: Path) -> None:
    client = _build_client(tmp_path)
    response = client.post(
        "/assets/licenses",
        data={
            "name": "Missing No",
            "license_key": "KEY-200",
            "state": "active",
            "note": "",
        },
    )
    assert response.status_code == 422


def test_create_license_key_boundaries(tmp_path: Path) -> None:
    client = _build_client(tmp_path)
    response = client.post(
        "/assets/licenses",
        data={
            "license_no": "LIC-MIN",
            "name": "MinKey",
            "license_key": "K",
            "state": "active",
            "note": "",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    long_key = "K" * 255
    response = client.post(
        "/assets/licenses",
        data={
            "license_no": "LIC-MAX",
            "name": "MaxKey",
            "license_key": long_key,
            "state": "active",
            "note": "",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    page = client.get("/assets/licenses")
    assert "LIC-MIN" in page.text
    assert "LIC-MAX" in page.text


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
    assert "DEV-001" in response.text
    assert "LIC-001" in response.text


def test_assign_device(tmp_path: Path) -> None:
    client, db_path = _build_client_with_db(tmp_path)
    response = client.post(
        "/api/configs/1/assign",
        json={"asset_type": "device", "asset_id": 9, "source_config_id": None},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    row = _fetch_one(
        db_path,
        "SELECT config_id FROM config_devices WHERE device_id = ?",
        (9,),
    )
    assert row is not None
    assert int(row["config_id"]) == 1


def test_assign_device_conflict(tmp_path: Path) -> None:
    client = _build_client(tmp_path)
    response = client.post(
        "/api/configs/2/assign",
        json={"asset_type": "device", "asset_id": 1, "source_config_id": None},
    )
    assert response.status_code == 409


def test_save_position(tmp_path: Path) -> None:
    client, db_path = _build_client_with_db(tmp_path)
    response = client.post(
        "/api/configs/1/position",
        json={"x": 120, "y": 240},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    row = _fetch_one(
        db_path,
        "SELECT x, y FROM config_positions WHERE config_id = ?",
        (1,),
    )
    assert row is not None
    assert float(row["x"]) == 120
    assert float(row["y"]) == 240


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


def test_device_search_and_sort(tmp_path: Path) -> None:
    client = _build_client(tmp_path)
    client.post(
        "/assets/devices",
        data={
            "asset_no": "DEV-AAA",
            "display_name": "SearchTarget",
            "device_type": "PC",
            "model": "Model-A",
            "version": "2025",
            "state": "active",
            "note": "",
        },
        follow_redirects=False,
    )
    client.post(
        "/assets/devices",
        data={
            "asset_no": "DEV-BBB",
            "display_name": "Other",
            "device_type": "PC",
            "model": "Model-B",
            "version": "2025",
            "state": "active",
            "note": "",
        },
        follow_redirects=False,
    )
    response = client.get("/assets/devices?device_q=SearchTarget")
    assert "DEV-AAA" in response.text
    assert "DEV-BBB" not in response.text
    response = client.get("/assets/devices?device_sort=asset_no&device_dir=asc")
    assert response.text.find("DEV-AAA") < response.text.find("DEV-BBB")


def test_device_update_double_submit(tmp_path: Path) -> None:
    client, db_path = _build_client_with_db(tmp_path)
    client.post(
        "/assets/devices",
        data={
            "asset_no": "DEV-UPDATE",
            "display_name": "Before",
            "device_type": "PC",
            "model": "Model-U",
            "version": "2025",
            "state": "active",
            "note": "",
        },
        follow_redirects=False,
    )
    row = _fetch_one(db_path, "SELECT device_id FROM devices WHERE asset_no = ?", ("DEV-UPDATE",))
    assert row is not None
    device_id = int(row["device_id"])
    response = client.post(
        f"/assets/devices/{device_id}/edit",
        data={
            "asset_no": "DEV-UPDATE",
            "display_name": "Update-1",
            "device_type": "PC",
            "model": "Model-U",
            "version": "2025",
            "state": "active",
            "note": "",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    response = client.post(
        f"/assets/devices/{device_id}/edit",
        data={
            "asset_no": "DEV-UPDATE",
            "display_name": "Update-2",
            "device_type": "PC",
            "model": "Model-U",
            "version": "2025",
            "state": "active",
            "note": "",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    page = client.get("/assets/devices")
    assert "Update-2" in page.text


def test_device_delete(tmp_path: Path) -> None:
    client, db_path = _build_client_with_db(tmp_path)
    client.post(
        "/assets/devices",
        data={
            "asset_no": "DEV-DELETE",
            "display_name": "Delete",
            "device_type": "PC",
            "model": "Model-D",
            "version": "2025",
            "state": "active",
            "note": "",
        },
        follow_redirects=False,
    )
    row = _fetch_one(db_path, "SELECT device_id FROM devices WHERE asset_no = ?", ("DEV-DELETE",))
    assert row is not None
    device_id = int(row["device_id"])
    response = client.post(f"/assets/devices/{device_id}/delete", follow_redirects=False)
    assert response.status_code == 303
    page = client.get("/assets/devices")
    assert "DEV-DELETE" not in page.text


def test_license_search_sort_update_delete(tmp_path: Path) -> None:
    client, db_path = _build_client_with_db(tmp_path)
    client.post(
        "/assets/licenses",
        data={
            "license_no": "LIC-AAA",
            "name": "SearchLicense",
            "license_key": "KEY-AAA",
            "state": "active",
            "note": "",
        },
        follow_redirects=False,
    )
    client.post(
        "/assets/licenses",
        data={
            "license_no": "LIC-BBB",
            "name": "Other",
            "license_key": "KEY-BBB",
            "state": "active",
            "note": "",
        },
        follow_redirects=False,
    )
    response = client.get("/assets/licenses?license_q=SearchLicense")
    assert "LIC-AAA" in response.text
    assert "LIC-BBB" not in response.text
    response = client.get("/assets/licenses?license_sort=license_no&license_dir=asc")
    assert response.text.find("LIC-AAA") < response.text.find("LIC-BBB")
    row = _fetch_one(db_path, "SELECT license_id FROM licenses WHERE license_no = ?", ("LIC-AAA",))
    assert row is not None
    license_id = int(row["license_id"])
    response = client.post(
        f"/assets/licenses/{license_id}/edit",
        data={
            "license_no": "LIC-AAA",
            "name": "Updated-1",
            "license_key": "KEY-AAA",
            "state": "active",
            "note": "",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    response = client.post(
        f"/assets/licenses/{license_id}/edit",
        data={
            "license_no": "LIC-AAA",
            "name": "Updated-2",
            "license_key": "KEY-AAA",
            "state": "active",
            "note": "",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    page = client.get("/assets/licenses")
    assert "Updated-2" in page.text
    response = client.post(f"/assets/licenses/{license_id}/delete", follow_redirects=False)
    assert response.status_code == 303
    page = client.get("/assets/licenses")
    assert "LIC-AAA" not in page.text


def test_config_create_required_and_boundaries(tmp_path: Path) -> None:
    client = _build_client(tmp_path)
    response = client.post("/configurations", data={"note": "missing"})
    assert response.status_code == 422
    response = client.post("/configurations", data={"name": "A", "note": ""}, follow_redirects=False)
    assert response.status_code == 303
    long_name = "X" * 255
    response = client.post("/configurations", data={"name": long_name, "note": ""}, follow_redirects=False)
    assert response.status_code == 303
    page = client.get("/configurations")
    assert "A" in page.text
    assert long_name in page.text


def test_config_update_delete(tmp_path: Path) -> None:
    client, db_path = _build_client_with_db(tmp_path)
    response = client.post(
        "/configurations",
        data={"name": "更新前-構成", "note": "note"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    row = _fetch_one(db_path, "SELECT config_id FROM configurations WHERE name = ?", ("更新前-構成",))
    assert row is not None
    config_id = int(row["config_id"])
    response = client.post(
        f"/configurations/{config_id}/edit",
        data={"name": "更新後-構成", "note": "note2"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    page = client.get("/configurations")
    assert "更新後-構成" in page.text
    response = client.post(f"/configurations/{config_id}/delete", follow_redirects=False)
    assert response.status_code == 303
    page = client.get("/configurations")
    assert "更新後-構成" not in page.text


def test_assign_license(tmp_path: Path) -> None:
    client, db_path = _build_client_with_db(tmp_path)
    response = client.post(
        "/api/configs/1/assign",
        json={"asset_type": "license", "asset_id": 9, "source_config_id": None},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    row = _fetch_one(
        db_path,
        "SELECT config_id FROM config_licenses WHERE license_id = ?",
        (9,),
    )
    assert row is not None
    assert int(row["config_id"]) == 1


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
