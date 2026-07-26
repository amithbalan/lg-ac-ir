"""Config flow for the LG AC Infrared integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.infrared import async_get_emitters
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
)

from .const import (
    CONF_INFRARED_ENTITY_ID,
    DEFAULT_NAME,
    DOMAIN,
    INFRARED_DOMAIN,
)


class LgAcIrConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for LG AC Infrared."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step: pick the infrared emitter."""
        emitters = async_get_emitters(self.hass)
        if not emitters:
            # No IR emitter exists yet - guide the user to set one up first.
            return self.async_abort(reason="no_emitters")

        if user_input is not None:
            # One AC per emitter keeps overlapping transmissions unambiguous.
            await self.async_set_unique_id(user_input[CONF_INFRARED_ENTITY_ID])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input.get(CONF_NAME, DEFAULT_NAME),
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_INFRARED_ENTITY_ID): EntitySelector(
                    EntitySelectorConfig(
                        domain=INFRARED_DOMAIN,
                        include_entities=emitters,
                    )
                ),
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)
