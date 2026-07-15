"""Config flow for NGBS iCON."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback

from .api import NgbsClient, NgbsError
from .const import (
    CONF_SCAN_INTERVAL,
    CONF_SYSID,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)


class NgbsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NGBS iCON."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            client = NgbsClient(user_input[CONF_HOST], user_input[CONF_PORT])
            try:
                sysid = await client.discover_sysid()
                state = await client.get_state(include_config=True)
            except NgbsError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(sysid)
                self._abort_if_unique_id_configured(updates={CONF_HOST: user_input[CONF_HOST]})
                cfg = state.get("CFG") or {}
                return self.async_create_entry(
                    title=str(cfg.get("NAME") or f"NGBS iCON {sysid}"),
                    data={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_PORT: user_input[CONF_PORT],
                        CONF_SYSID: sysid,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return NgbsOptionsFlow()


class NgbsOptionsFlow(config_entries.OptionsFlow):
    """Handle NGBS options."""

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): vol.All(int, vol.Range(min=5, max=300))
                }
            ),
        )
