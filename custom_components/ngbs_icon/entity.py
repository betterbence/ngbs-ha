"""Base entities for NGBS iCON."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NgbsCoordinator


class NgbsControllerEntity(CoordinatorEntity[NgbsCoordinator]):
    """Base entity attached to the controller device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: NgbsCoordinator) -> None:
        super().__init__(coordinator)
        state = coordinator.data
        sysid = str(state.get("SYSID", coordinator.client.sysid or "unknown"))
        cfg = state.get("CFG") or {}
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, sysid)},
            name=str(cfg.get("NAME") or "NGBS iCON"),
            manufacturer="NGBS",
            model="iCON",
            sw_version=str((state.get("INFO") or {}).get("FIRMWARE") or state.get("VER") or ""),
            configuration_url=f"http://{coordinator.client.host}",
        )


class NgbsThermostatEntity(CoordinatorEntity[NgbsCoordinator]):
    """Base entity attached to a thermostat device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: NgbsCoordinator, thermostat_id: str) -> None:
        super().__init__(coordinator)
        self.thermostat_id = thermostat_id
        state = coordinator.data
        sysid = str(state.get("SYSID", coordinator.client.sysid or "unknown"))
        th = (state.get("DP") or {}).get(thermostat_id, {})
        name = str(th.get("NAME") or f"Thermostat {thermostat_id}").strip()
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{sysid}_{thermostat_id}")},
            name=name,
            manufacturer="NGBS",
            model="iCON thermostat",
            via_device=(DOMAIN, sysid),
        )

    @property
    def thermostat(self) -> dict[str, Any]:
        return (self.coordinator.data.get("DP") or {}).get(self.thermostat_id, {})
