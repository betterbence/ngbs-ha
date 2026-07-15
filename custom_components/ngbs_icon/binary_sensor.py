"""Binary sensors for NGBS iCON."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity, BinarySensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import NgbsCoordinator
from .entity import NgbsControllerEntity, NgbsThermostatEntity


@dataclass(frozen=True, kw_only=True)
class NgbsBinaryDescription(BinarySensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], bool]


THERMOSTAT_BINARY = (
    NgbsBinaryDescription(key="online", translation_key="online", device_class=BinarySensorDeviceClass.CONNECTIVITY, value_fn=lambda th: th.get("LIVE") == 1),
    NgbsBinaryDescription(key="valve", translation_key="valve", device_class=BinarySensorDeviceClass.RUNNING, value_fn=lambda th: th.get("OUT") == 1),
    NgbsBinaryDescription(key="dew_protection", translation_key="dew_protection", device_class=BinarySensorDeviceClass.PROBLEM, value_fn=lambda th: th.get("DWP") == 1),
    NgbsBinaryDescription(key="frost", translation_key="frost", device_class=BinarySensorDeviceClass.PROBLEM, value_fn=lambda th: th.get("FROST") == 1),
)

CONTROLLER_BINARY = (
    NgbsBinaryDescription(key="pump", translation_key="pump", device_class=BinarySensorDeviceClass.RUNNING, value_fn=lambda state: state.get("PUMP") == 1),
    NgbsBinaryDescription(key="overheat", translation_key="overheat", device_class=BinarySensorDeviceClass.PROBLEM, value_fn=lambda state: state.get("OVERHEAT") == 1),
    NgbsBinaryDescription(key="water_frost", translation_key="water_frost", device_class=BinarySensorDeviceClass.PROBLEM, value_fn=lambda state: state.get("WFROST") == 1),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    coordinator: NgbsCoordinator = entry.runtime_data
    entities: list[BinarySensorEntity] = [NgbsControllerBinary(coordinator, desc) for desc in CONTROLLER_BINARY]
    for th_id, th in (coordinator.data.get("DP") or {}).items():
        if th.get("ON") == 1 and th.get("LIVE") == 1:
            entities.extend(NgbsThermostatBinary(coordinator, str(th_id), desc) for desc in THERMOSTAT_BINARY)
    async_add_entities(entities)


class NgbsControllerBinary(NgbsControllerEntity, BinarySensorEntity):
    entity_description: NgbsBinaryDescription
    def __init__(self, coordinator, description):
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.client.sysid}_controller_{description.key}"
    @property
    def is_on(self):
        return self.entity_description.value_fn(self.coordinator.data)


class NgbsThermostatBinary(NgbsThermostatEntity, BinarySensorEntity):
    entity_description: NgbsBinaryDescription
    def __init__(self, coordinator, thermostat_id, description):
        super().__init__(coordinator, thermostat_id)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.client.sysid}_{thermostat_id}_{description.key}"
    @property
    def is_on(self):
        return self.entity_description.value_fn(self.thermostat)
