"""Select entities for NGBS iCON."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import NgbsCoordinator
from .entity import NgbsControllerEntity

MODE_HEATING = "heating"
MODE_COOLING = "cooling"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator: NgbsCoordinator = entry.runtime_data
    async_add_entities([NgbsOperatingModeSelect(coordinator)])


class NgbsOperatingModeSelect(NgbsControllerEntity, SelectEntity):
    """Global heating/cooling operating mode."""

    _attr_translation_key = "operating_mode"
    _attr_icon = "mdi:heat-wave"
    _attr_options = [MODE_HEATING, MODE_COOLING]

    def __init__(self, coordinator: NgbsCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.client.sysid}_operating_mode"

    @property
    def current_option(self) -> str:
        return MODE_COOLING if self.coordinator.data.get("HC") == 1 else MODE_HEATING

    async def async_select_option(self, option: str) -> None:
        if option not in self.options:
            raise HomeAssistantError(f"Unsupported operating mode: {option}")
        await self.coordinator.async_command(
            self.coordinator.client.set_global_cooling,
            option == MODE_COOLING,
        )
