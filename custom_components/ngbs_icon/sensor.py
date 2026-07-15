"""Sensors for NGBS iCON."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import NgbsCoordinator
from .entity import NgbsControllerEntity, NgbsThermostatEntity


@dataclass(frozen=True, kw_only=True)
class NgbsSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any]


THERMOSTAT_SENSORS = (
    NgbsSensorDescription(key="humidity", translation_key="humidity", device_class=SensorDeviceClass.HUMIDITY, native_unit_of_measurement=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT, value_fn=lambda th: th.get("RH")),
    NgbsSensorDescription(key="dew_point", translation_key="dew_point", device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT, value_fn=lambda th: th.get("DEW")),
)

CONTROLLER_SENSORS = (
    NgbsSensorDescription(key="water_temperature", translation_key="water_temperature", device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT, value_fn=lambda state: state.get("WTEMP")),
    NgbsSensorDescription(key="outside_temperature", translation_key="outside_temperature", device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT, value_fn=lambda state: state.get("ETEMP")),
    NgbsSensorDescription(key="uptime", translation_key="uptime", device_class=SensorDeviceClass.DURATION, native_unit_of_measurement=UnitOfTime.HOURS, value_fn=lambda state: (state.get("INFO") or {}).get("UPTIME")),
    NgbsSensorDescription(key="mixing_valve", translation_key="mixing_valve", native_unit_of_measurement=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT, value_fn=lambda state: ((((state.get("CFG") or {}).get("ICON1") or {}).get("STATUS") or {}).get("AO"))),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    coordinator: NgbsCoordinator = entry.runtime_data
    entities: list[SensorEntity] = [NgbsControllerSensor(coordinator, desc) for desc in CONTROLLER_SENSORS]
    for th_id, th in (coordinator.data.get("DP") or {}).items():
        if th.get("ON") == 1 and th.get("LIVE") == 1:
            entities.extend(NgbsThermostatSensor(coordinator, str(th_id), desc) for desc in THERMOSTAT_SENSORS)
    async_add_entities(entities)


class NgbsControllerSensor(NgbsControllerEntity, SensorEntity):
    entity_description: NgbsSensorDescription
    def __init__(self, coordinator, description):
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.client.sysid}_controller_{description.key}"
    @property
    def native_value(self):
        return self.entity_description.value_fn(self.coordinator.data)


class NgbsThermostatSensor(NgbsThermostatEntity, SensorEntity):
    entity_description: NgbsSensorDescription
    def __init__(self, coordinator, thermostat_id, description):
        super().__init__(coordinator, thermostat_id)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.client.sysid}_{thermostat_id}_{description.key}"
    @property
    def native_value(self):
        return self.entity_description.value_fn(self.thermostat)
