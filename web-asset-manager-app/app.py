from __future__ import annotations

import os
import sys
from typing import Dict, List, Optional

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel


def _ensure_src_path() -> None:
    root = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.join(root, "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)


_ensure_src_path()

from wam.db import init_db  # noqa: E402
from wam.repositories import ConfigRepository, DeviceRepository, LicenseRepository, PositionRepository  # noqa: E402
from wam.services import AssetService, ConfigService  # noqa: E402


class AssignPayload(BaseModel):
    asset_type: str
    asset_id: int
    source_config_id: Optional[int] = None


class PositionPayload(BaseModel):
    x: float
    y: float


def _default_db_path() -> str:
    root = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(root, "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "wam.sqlite3")


def create_app(db_path: Optional[str] = None) -> FastAPI:
    db_path = db_path or os.environ.get("WAM_DB_PATH") or _default_db_path()
    conn = init_db(db_path)

    device_repo = DeviceRepository(conn)
    license_repo = LicenseRepository(conn)
    config_repo = ConfigRepository(conn)
    position_repo = PositionRepository(conn)

    asset_service = AssetService(device_repo, license_repo)
    config_service = ConfigService(config_repo)

    app = FastAPI(title="Web Asset Manager", version="1.0.0")

    templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "web", "templates"))
    app.mount(
        "/static",
        StaticFiles(directory=os.path.join(os.path.dirname(__file__), "web", "static")),
        name="static",
    )

    @app.get("/", response_class=HTMLResponse)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/assets")

    @app.get("/assets", response_class=HTMLResponse)
    def assets(request: Request) -> HTMLResponse:
        devices = asset_service.list_devices()
        licenses = asset_service.list_licenses()
        return templates.TemplateResponse(
            request,
            "assets.html",
            {
                "request": request,
                "device_count": len(devices),
                "license_count": len(licenses),
            },
        )

    @app.get("/assets/devices", response_class=HTMLResponse)
    def device_list(
        request: Request,
        device_q: str | None = None,
        device_sort: str | None = None,
        device_dir: str | None = None,
    ) -> HTMLResponse:
        devices = asset_service.list_devices()

        if device_q:
            query = device_q.lower()
            devices = [
                item
                for item in devices
                if query in item.asset_no.lower()
                or query in (item.display_name or "").lower()
                or query in item.device_type.lower()
                or query in item.model.lower()
                or query in item.version.lower()
                or query in item.state.lower()
            ]

        device_sort_map = {
            "asset_no": lambda item: item.asset_no,
            "display_name": lambda item: item.display_name or "",
            "device_type": lambda item: item.device_type,
            "model": lambda item: item.model,
            "version": lambda item: item.version,
            "state": lambda item: item.state,
        }
        if device_sort in device_sort_map:
            devices = sorted(devices, key=device_sort_map[device_sort], reverse=device_dir == "desc")

        return templates.TemplateResponse(
            request,
            "devices.html",
            {
                "request": request,
                "devices": devices,
                "device_q": device_q or "",
                "device_sort": device_sort or "",
                "device_dir": device_dir or "",
            },
        )

    @app.get("/assets/devices/new", response_class=HTMLResponse)
    def new_device_form(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request,
            "device_create.html",
            {"request": request},
        )

    @app.get("/assets/licenses", response_class=HTMLResponse)
    def license_list(
        request: Request,
        license_q: str | None = None,
        license_sort: str | None = None,
        license_dir: str | None = None,
    ) -> HTMLResponse:
        licenses = asset_service.list_licenses()

        if license_q:
            query = license_q.lower()
            licenses = [
                item
                for item in licenses
                if query in item.license_no.lower()
                or query in item.name.lower()
                or query in item.license_key.lower()
                or query in item.state.lower()
            ]

        license_sort_map = {
            "license_no": lambda item: item.license_no,
            "name": lambda item: item.name,
            "license_key": lambda item: item.license_key,
            "state": lambda item: item.state,
        }
        if license_sort in license_sort_map:
            licenses = sorted(licenses, key=license_sort_map[license_sort], reverse=license_dir == "desc")

        return templates.TemplateResponse(
            request,
            "licenses.html",
            {
                "request": request,
                "licenses": licenses,
                "license_q": license_q or "",
                "license_sort": license_sort or "",
                "license_dir": license_dir or "",
            },
        )

    @app.get("/assets/licenses/new", response_class=HTMLResponse)
    def new_license_form(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request,
            "license_create.html",
            {"request": request},
        )

    @app.post("/assets/devices")
    def create_device(
        asset_no: str = Form(...),
        display_name: Optional[str] = Form(None),
        device_type: str = Form(...),
        model: str = Form(...),
        version: str = Form(...),
        state: str = Form(...),
        note: str = Form(""),
    ) -> RedirectResponse:
        asset_service.add_device(
            asset_no=asset_no,
            display_name=display_name,
            device_type=device_type,
            model=model,
            version=version,
            state=state,
            note=note,
        )
        return RedirectResponse(url="/assets/devices", status_code=303)

    @app.get("/assets/devices/{device_id}/edit", response_class=HTMLResponse)
    def edit_device_form(request: Request, device_id: int) -> HTMLResponse:
        device = device_repo.get_by_id(device_id)
        return templates.TemplateResponse(
            request,
            "device_edit.html",
            {"request": request, "device": device},
        )

    @app.post("/assets/devices/{device_id}/edit")
    def edit_device(
        device_id: int,
        asset_no: str = Form(...),
        display_name: Optional[str] = Form(None),
        device_type: str = Form(...),
        model: str = Form(...),
        version: str = Form(...),
        state: str = Form(...),
        note: str = Form(""),
    ) -> RedirectResponse:
        asset_service.update_device(
            device_id=device_id,
            asset_no=asset_no,
            display_name=display_name,
            device_type=device_type,
            model=model,
            version=version,
            state=state,
            note=note,
        )
        return RedirectResponse(url="/assets/devices", status_code=303)

    @app.post("/assets/devices/{device_id}/delete")
    def delete_device(device_id: int) -> RedirectResponse:
        asset_service.delete_device(device_id)
        return RedirectResponse(url="/assets/devices", status_code=303)

    @app.post("/assets/licenses")
    def create_license(
        license_no: str = Form(...),
        name: str = Form(...),
        license_key: str = Form(...),
        state: str = Form(...),
        note: str = Form(""),
    ) -> RedirectResponse:
        asset_service.add_license(
            license_no=license_no,
            name=name,
            license_key=license_key,
            state=state,
            note=note,
        )
        return RedirectResponse(url="/assets/licenses", status_code=303)

    @app.get("/assets/licenses/{license_id}/edit", response_class=HTMLResponse)
    def edit_license_form(request: Request, license_id: int) -> HTMLResponse:
        license_item = license_repo.get_by_id(license_id)
        return templates.TemplateResponse(
            request,
            "license_edit.html",
            {"request": request, "license": license_item},
        )

    @app.post("/assets/licenses/{license_id}/edit")
    def edit_license(
        license_id: int,
        license_no: str = Form(...),
        name: str = Form(...),
        license_key: str = Form(...),
        state: str = Form(...),
        note: str = Form(""),
    ) -> RedirectResponse:
        asset_service.update_license(
            license_id=license_id,
            license_no=license_no,
            name=name,
            license_key=license_key,
            state=state,
            note=note,
        )
        return RedirectResponse(url="/assets/licenses", status_code=303)

    @app.post("/assets/licenses/{license_id}/delete")
    def delete_license(license_id: int) -> RedirectResponse:
        asset_service.delete_license(license_id)
        return RedirectResponse(url="/assets/licenses", status_code=303)

    @app.get("/configurations", response_class=HTMLResponse)
    def configurations(
        request: Request,
        config_q: str | None = None,
        config_sort: str | None = None,
        config_dir: str | None = None,
    ) -> HTMLResponse:
        configs = config_service.list_configs()
        if config_q:
            query = config_q.lower()
            configs = [
                item
                for item in configs
                if query in item.config_no.lower() or query in item.name.lower() or query in item.note.lower()
            ]
        config_sort_map = {
            "config_no": lambda item: item.config_no,
            "name": lambda item: item.name,
            "created_at": lambda item: item.created_at,
            "updated_at": lambda item: item.updated_at,
        }
        if config_sort in config_sort_map:
            configs = sorted(configs, key=config_sort_map[config_sort], reverse=config_dir == "desc")
        assigned_device_ids = set(config_service.list_assigned_device_ids())
        assigned_license_ids = set(config_service.list_assigned_license_ids())

        devices = asset_service.list_devices()
        licenses = asset_service.list_licenses()

        available_devices = [device for device in devices if device.device_id not in assigned_device_ids]
        available_licenses = [license_item for license_item in licenses if license_item.license_id not in assigned_license_ids]

        positions = position_repo.load_positions()
        config_cards: List[Dict[str, object]] = []
        for index, config in enumerate(configs):
            config_devices = config_service.list_config_devices(config.config_id)
            config_licenses = config_service.list_config_licenses(config.config_id)
            pos = positions.get(config.config_id)
            if pos:
                x, y, hidden = pos
                if hidden:
                    continue
            else:
                x = 40 + (index % 3) * 340
                y = 40 + (index // 3) * 260
            config_cards.append(
                {
                    "config": config,
                    "devices": config_devices,
                    "licenses": config_licenses,
                    "x": x,
                    "y": y,
                }
            )

        return templates.TemplateResponse(
            request,
            "configurations.html",
            {
                "request": request,
                "configs": config_cards,
                "available_devices": available_devices,
                "available_licenses": available_licenses,
                "config_q": config_q or "",
                "config_sort": config_sort or "",
                "config_dir": config_dir or "",
            },
        )

    @app.get("/configurations/{config_id}", response_class=HTMLResponse)
    def configuration_detail(request: Request, config_id: int) -> HTMLResponse:
        config = config_repo.get_by_id(config_id)
        config_devices = config_service.list_config_devices(config_id)
        config_licenses = config_service.list_config_licenses(config_id)
        return templates.TemplateResponse(
            request,
            "config_detail.html",
            {
                "request": request,
                "config": config,
                "devices": config_devices,
                "licenses": config_licenses,
            },
        )

    @app.post("/configurations")
    def create_configuration(
        name: str = Form(...),
        note: str = Form(""),
    ) -> RedirectResponse:
        config_service.create_config(name=name, note=note)
        return RedirectResponse(url="/configurations", status_code=303)

    @app.get("/configurations/{config_id}/edit", response_class=HTMLResponse)
    def edit_config_form(request: Request, config_id: int) -> HTMLResponse:
        config = config_repo.get_by_id(config_id)
        return templates.TemplateResponse(
            request,
            "config_edit.html",
            {"request": request, "config": config},
        )

    @app.post("/configurations/{config_id}/edit")
    def edit_config(config_id: int, name: str = Form(...), note: str = Form("")) -> RedirectResponse:
        config_service.update_config(config_id, name, note)
        return RedirectResponse(url="/configurations", status_code=303)

    @app.post("/configurations/{config_id}/delete")
    def delete_config(config_id: int) -> RedirectResponse:
        config_service.delete_config(config_id)
        return RedirectResponse(url="/configurations", status_code=303)

    @app.post("/api/configs/{config_id}/assign", response_class=JSONResponse)
    def assign_asset(config_id: int, payload: AssignPayload) -> JSONResponse:
        if payload.asset_type == "device":
            if payload.source_config_id and payload.source_config_id != config_id:
                config_service.move_device(payload.source_config_id, config_id, payload.asset_id)
            else:
                owner = config_service.get_device_owner(payload.asset_id)
                if owner is not None and owner != config_id:
                    raise HTTPException(status_code=409, detail="Device already assigned")
                config_service.assign_device(config_id, payload.asset_id)
            return JSONResponse({"status": "ok"})

        if payload.asset_type == "license":
            if payload.source_config_id and payload.source_config_id != config_id:
                config_service.unassign_license(payload.source_config_id, payload.asset_id)
                config_service.assign_license(config_id, payload.asset_id)
            else:
                owner = config_service.get_license_owner(payload.asset_id)
                if owner is not None and owner != config_id:
                    raise HTTPException(status_code=409, detail="License already assigned")
                config_service.assign_license(config_id, payload.asset_id)
            return JSONResponse({"status": "ok"})

        raise HTTPException(status_code=400, detail="Unknown asset type")

    @app.post("/api/configs/{config_id}/position", response_class=JSONResponse)
    def save_position(config_id: int, payload: PositionPayload) -> JSONResponse:
        position_repo.save_position(config_id, payload.x, payload.y)
        return JSONResponse({"status": "ok"})

    @app.get("/api/summary", response_class=JSONResponse)
    def summary() -> JSONResponse:
        devices = asset_service.list_devices()
        licenses = asset_service.list_licenses()
        configs = config_service.list_configs()
        return JSONResponse(
            {
                "devices": len(devices),
                "licenses": len(licenses),
                "configs": len(configs),
            }
        )

    @app.get("/health", response_class=JSONResponse)
    def health() -> JSONResponse:
        return JSONResponse({"status": "ok"})

    return app


app = create_app()
