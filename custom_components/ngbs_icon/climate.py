"""Climate entities for NGBS iCON thermostats."""

from __future__ import annotations

from typing import Any

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import ClimateEntityFeature, HVACAction, HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import NgbsCoordinator
from .entity import NgbsThermostatEntity

PRESET_COMFORT = "comfort"
PRESET_ECO = "eco"


def _enabled_thermostats(data: dict[str, Any]) -> list[str]:
    return [
        str(key)
        for key, value in (data.get("DP") or {}).items()
        if value.get("ON") == 1 and value.get("LIVE") == 1
    ]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator: NgbsCoordinator = entry.runtime_data
    async_add_entities(NgbsClimate(coordinator, th_id) for th_id in _enabled_thermostats(coordinator.data))


class NgbsClimate(NgbsThermostatEntity, ClimateEntity):
    """NGBS thermostat climate entity."""

    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 0.5
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.COOL]
    _attr_preset_modes = [PRESET_COMFORT, PRESET_ECO]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
    )

    def __init__(self, coordinator: NgbsCoordinator, thermostat_id: str) -> None:
        super().__init__(coordinator, thermostat_id)
        self._attr_unique_id = f"{coordinator.client.sysid}_{thermostat_id}_climate"

    @property
    def available(self) -> bool:
        return super().available and self.thermostat.get("LIVE") == 1

    @property
    def current_temperature(self) -> float | None:
        value = self.thermostat.get("TEMP")
        return float(value) if value is not None else None

    @property
    def current_humidity(self) -> float | None:
        value = self.thermostat.get("RH")
        return float(value) if value is not None else None

    @property
    def target_temperature(self) -> float | None:
        th = self.thermostat
        field = "ECOC" if th.get("CE") and th.get("HC") else "ECOH" if th.get("CE") else "XAC" if th.get("HC") else "XAH"
        value = th.get(field)
        return float(value) if value is not None else None

    @property
    def min_temp(self) -> float:
        midpoint = self._midpoint
        return max(5.0, midpoint - float(self.thermostat.get("LIM", 5)))

    @property
    def max_temp(self) -> float:
        midpoint = self._midpoint
        return min(45.0, midpoint + float(self.thermostat.get("LIM", 5)))

    @property
    def _midpoint(self) -> float:
        state = self.coordinator.data
        th = self.thermostat
        field = "ECOC" if th.get("CE") and th.get("HC") else "ECOH" if th.get("CE") else "XAC" if th.get("HC") else "XAH"
        return float(state.get(field, 22))

    @property
    def hvac_mode(self) -> HVACMode:
        return HVACMode.COOL if self.thermostat.get("HC") == 1 else HVACMode.HEAT

    @property
    def hvac_action(self):
        if self.thermostat.get("OUT") != 1:
            return HVACAction.IDLE
        return HVACAction.COOLING if self.thermostat.get("HC") == 1 else HVACAction.HEATING

    @property
    def preset_mode(self) -> str:
        return PRESET_ECO if self.thermostat.get("CE") == 1 else PRESET_COMFORT

    async def async_set_temperature(self, **kwargs: Any) -> None:
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        await self.coordinator.async_command(
            self.coordinator.client.set_thermostat_target,
            self.thermostat_id,
            float(temperature),
        )

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        if preset_mode not in self.preset_modes:
            raise HomeAssistantError(f"Unsupported preset mode: {preset_mode}")
        await self.coordinator.async_command(
            self.coordinator.client.set_thermostat_eco,
            self.thermostat_id,
            preset_mode == PRESET_ECO,
        )

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        cfg = self.coordinator.data.get("CFG") or {}
        master = str(cfg.get("HCMASTER", "")).removeprefix("H")
        if master and master != self.thermostat_id:
            raise HomeAssistantError("Heating/cooling mode can only be changed on the master thermostat")
        if hvac_mode not in (HVACMode.HEAT, HVACMode.COOL):
            raise HomeAssistantError(f"Unsupported HVAC mode: {hvac_mode}")
        await self.coordinator.async_command(
            self.coordinator.client.set_global_cooling,
            hvac_mode == HVACMode.COOL,
        )
