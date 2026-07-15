"""The NGBS iCON integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant

from .api import NgbsClient
from .const import CONF_SYSID, DEFAULT_PORT, DEFAULT_TIMEOUT, PLATFORMS
from .coordinator import NgbsCoordinator


type NgbsConfigEntry = ConfigEntry[NgbsCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: NgbsConfigEntry) -> bool:
    """Set up NGBS iCON from a config entry."""
    client = NgbsClient(
        host=entry.data[CONF_HOST],
        port=entry.data.get(CONF_PORT, DEFAULT_PORT),
        timeout=DEFAULT_TIMEOUT,
        sysid=entry.data[CONF_SYSID],
    )
    coordinator = NgbsCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: NgbsConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
