from __future__ import annotations

from typing import List, Optional

from wam.models import Configuration, Device, License
from wam.repositories import ConfigRepository, DeviceRepository, LicenseRepository


class AssetService:
    def __init__(self, device_repo: DeviceRepository, license_repo: LicenseRepository) -> None:
        self._device_repo = device_repo
        self._license_repo = license_repo

    def add_device(
        self,
        asset_no: str,
        display_name: Optional[str],
        device_type: str,
        model: str,
        version: str,
        state: str,
        note: str,
    ) -> Device:
        return self._device_repo.create(
            asset_no=asset_no,
            display_name=display_name,
            device_type=device_type,
            model=model,
            version=version,
            state=state,
            note=note,
        )

    def list_devices(self) -> List[Device]:
        return self._device_repo.list_all()

    def update_device(
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
        return self._device_repo.update(
            device_id=device_id,
            asset_no=asset_no,
            display_name=display_name,
            device_type=device_type,
            model=model,
            version=version,
            state=state,
            note=note,
        )

    def delete_device(self, device_id: int) -> None:
        self._device_repo.delete(device_id)

    def add_license(self, license_no: str, name: str, license_key: str, state: str, note: str) -> License:
        return self._license_repo.create(
            license_no=license_no,
            name=name,
            license_key=license_key,
            state=state,
            note=note,
        )

    def list_licenses(self) -> List[License]:
        return self._license_repo.list_all()

    def update_license(
        self,
        license_id: int,
        license_no: str,
        name: str,
        license_key: str,
        state: str,
        note: str,
    ) -> License:
        return self._license_repo.update(
            license_id=license_id,
            license_no=license_no,
            name=name,
            license_key=license_key,
            state=state,
            note=note,
        )

    def delete_license(self, license_id: int) -> None:
        self._license_repo.delete(license_id)


class ConfigService:
    def __init__(self, config_repo: ConfigRepository) -> None:
        self._config_repo = config_repo

    def create_config(self, name: str, note: str = "", config_no: str | None = None) -> Configuration:
        return self._config_repo.create(name=name, note=note, config_no=config_no)

    def list_configs(self) -> List[Configuration]:
        return self._config_repo.list_all()

    def update_config(self, config_id: int, name: str, note: str) -> Configuration:
        return self._config_repo.update(config_id, name, note)

    def delete_config(self, config_id: int) -> None:
        self._config_repo.delete(config_id)

    def list_config_devices(self, config_id: int) -> List[Device]:
        return self._config_repo.list_devices(config_id)

    def list_config_licenses(self, config_id: int) -> List[License]:
        return self._config_repo.list_licenses(config_id)

    def list_assigned_device_ids(self) -> List[int]:
        return self._config_repo.list_assigned_device_ids()

    def list_assigned_license_ids(self) -> List[int]:
        return self._config_repo.list_assigned_license_ids()

    def get_device_owner(self, device_id: int) -> int | None:
        return self._config_repo.get_device_owner(device_id)

    def get_license_owner(self, license_id: int) -> int | None:
        return self._config_repo.get_license_owner(license_id)

    def assign_device(self, config_id: int, device_id: int) -> None:
        self._config_repo.assign_device(config_id, device_id)

    def move_device(self, from_config_id: int, to_config_id: int, device_id: int) -> None:
        self._config_repo.move_device(from_config_id, to_config_id, device_id)

    def unassign_device(self, config_id: int, device_id: int) -> None:
        self._config_repo.unassign_device(config_id, device_id)

    def assign_license(self, config_id: int, license_id: int) -> None:
        self._config_repo.assign_license(config_id, license_id)

    def unassign_license(self, config_id: int, license_id: int) -> None:
        self._config_repo.unassign_license(config_id, license_id)
