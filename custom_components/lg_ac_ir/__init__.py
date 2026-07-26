"""The LG AC Infrared integration.

Exposes an LG air conditioner as a native Home Assistant climate entity,
transmitting through the `infrared` building-block platform (e.g. an ESPHome
`ir_rf_proxy` emitter). This is the AC counterpart to the built-in, TV-only
`lg_infrared` integration.
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

PLATFORMS: list[Platform] = [Platform.CLIMATE]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up LG AC Infrared from a config entry."""
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
