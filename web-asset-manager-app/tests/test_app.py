from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app import create_app


def _build_client(tmp_path: Path) -> TestClient:
    db_path = tmp_path / "test.sqlite3"
    app = create_app(str(db_path))
    return TestClient(app)


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
