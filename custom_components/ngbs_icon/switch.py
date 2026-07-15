"""Switches for NGBS iCON."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import NgbsCoordinator
from .entity import NgbsControllerEntity, NgbsThermostatEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    coordinator: NgbsCoordinator = entry.runtime_data
    entities: list[SwitchEntity] = [NgbsGlobalEcoSwitch(coordinator)]
    for th_id, th in (coordinator.data.get("DP") or {}).items():
        if th.get("ON") == 1 and th.get("LIVE") == 1:
            entities.append(NgbsParentalLockSwitch(coordinator, str(th_id)))
    async_add_entities(entities)


class NgbsGlobalEcoSwitch(NgbsControllerEntity, SwitchEntity):
    _attr_translation_key = "global_eco"
    _attr_icon = "mdi:leaf"
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.client.sysid}_global_eco"
    @property
    def is_on(self):
        return self.coordinator.data.get("CE") == 1
    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_command(self.coordinator.client.set_global_eco, True)
    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_command(self.coordinator.client.set_global_eco, False)


class NgbsParentalLockSwitch(NgbsThermostatEntity, SwitchEntity):
    _attr_translation_key = "parental_lock"
    _attr_icon = "mdi:lock"
    def __init__(self, coordinator, thermostat_id):
        super().__init__(coordinator, thermostat_id)
        self._attr_unique_id = f"{coordinator.client.sysid}_{thermostat_id}_parental_lock"
    @property
    def is_on(self):
        return self.thermostat.get("PL") == 1
    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_command(self.coordinator.client.set_parental_lock, self.thermostat_id, True)
    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_command(self.coordinator.client.set_parental_lock, self.thermostat_id, False)
