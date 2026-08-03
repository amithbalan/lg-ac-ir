"""Climate platform for the LG AC Infrared integration."""

from __future__ import annotations

import logging
from typing import Any

from ._lg_ac import (
    LgAcCommand,
    LgAcFanSpeed,
    LgAcMode,
)
from ._lg_ac_extra import (
    JET_COOL_FRAME,
    SWING_VERTICAL_FRAME,
    LgAcFixedCommand,
)

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.components.climate.const import (
    PRESET_BOOST,
    PRESET_NONE,
    SWING_OFF,
    SWING_VERTICAL,
)
from homeassistant.components.infrared import async_send_command
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, CONF_NAME, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_INFRARED_ENTITY_ID,
    DEFAULT_NAME,
    DOMAIN,
    MAX_TEMP,
    MIN_TEMP,
)

_LOGGER = logging.getLogger(__name__)

# Home Assistant HVAC mode -> LG AC protocol mode (OFF handled separately).
HVAC_TO_LG: dict[HVACMode, LgAcMode] = {
    HVACMode.COOL: LgAcMode.COOL,
    HVACMode.HEAT: LgAcMode.HEAT,
    HVACMode.DRY: LgAcMode.DRY,
    HVACMode.FAN_ONLY: LgAcMode.FAN_ONLY,
}

# Home Assistant fan mode -> LG fan speed.
FAN_TO_LG: dict[str, LgAcFanSpeed] = {
    "quiet": LgAcFanSpeed.QUIET,
    "low": LgAcFanSpeed.LOW,
    "medium": LgAcFanSpeed.MEDIUM,
    "high": LgAcFanSpeed.HIGH,
    "auto": LgAcFanSpeed.AUTO,
}

FAN_MODES = list(FAN_TO_LG)

# Modes for which the LG protocol carries a target temperature.
TEMPERATURE_MODES = (LgAcMode.COOL, LgAcMode.HEAT)

# Swing and Jet Cool are stateless toggle codes on the LG remote, so state is
# assumed: HA tracks the last commanded value and only fires the toggle frame
# when the value actually changes.
SWING_MODES = [SWING_OFF, SWING_VERTICAL]
PRESET_MODES = [PRESET_NONE, PRESET_BOOST]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the LG AC Infrared climate entity from a config entry."""
    async_add_entities([LgAcIrClimate(entry)])


class LgAcIrClimate(ClimateEntity):
    """An LG air conditioner driven over the infrared platform.

    IR is one-way: there is no feedback from the AC, so state is *assumed* -
    we track the last commanded state locally and re-transmit the full state
    on every change (LG ACs are stateless receivers; each frame is complete).
    """

    _attr_has_entity_name = True
    _attr_name = None
    _attr_should_poll = False
    _attr_assumed_state = True
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 1.0
    _attr_min_temp = MIN_TEMP
    _attr_max_temp = MAX_TEMP
    _attr_hvac_modes = [
        HVACMode.OFF,
        HVACMode.COOL,
        HVACMode.HEAT,
        HVACMode.DRY,
        HVACMode.FAN_ONLY,
    ]
    _attr_fan_modes = FAN_MODES
    _attr_swing_modes = SWING_MODES
    _attr_preset_modes = PRESET_MODES
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.SWING_MODE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialise the entity from its config entry."""
        self._emitter_id: str = entry.data[CONF_INFRARED_ENTITY_ID]
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data.get(CONF_NAME, DEFAULT_NAME),
            manufacturer="LG",
            model="Air Conditioner (IR)",
        )
        # Assumed initial state.
        self._attr_hvac_mode = HVACMode.OFF
        self._attr_target_temperature = 24
        self._attr_fan_mode = "auto"
        self._attr_swing_mode = SWING_OFF
        self._attr_preset_mode = PRESET_NONE
        # Mode to restore when turned on via the power toggle.
        self._last_on_mode = HVACMode.COOL

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set a new HVAC mode and transmit."""
        self._attr_hvac_mode = hvac_mode
        if hvac_mode is not HVACMode.OFF:
            self._last_on_mode = hvac_mode
        await self._transmit()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set a new target temperature and transmit."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return
        self._attr_target_temperature = int(temperature)
        # Setting a temperature while off implies powering on into the last mode.
        if self._attr_hvac_mode is HVACMode.OFF:
            self._attr_hvac_mode = self._last_on_mode
        await self._transmit()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set a new fan mode and transmit."""
        self._attr_fan_mode = fan_mode
        await self._transmit()

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        """Toggle vertical swing.

        LG sends a single fixed toggle frame; only fire it when the assumed
        state actually flips, so a no-op set doesn't desync the vane.
        """
        if swing_mode == self._attr_swing_mode:
            return
        self._attr_swing_mode = swing_mode
        await self._send_fixed(SWING_VERTICAL_FRAME)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Toggle Jet Cool (the LG 'boost' preset).

        Like swing, Jet Cool is a single toggle frame; fire it only on an actual
        change of the assumed preset state.
        """
        if preset_mode == self._attr_preset_mode:
            return
        self._attr_preset_mode = preset_mode
        await self._send_fixed(JET_COOL_FRAME)

    async def async_turn_on(self) -> None:
        """Turn the AC on, restoring the last active mode."""
        self._attr_hvac_mode = self._last_on_mode
        await self._transmit()

    async def async_turn_off(self) -> None:
        """Turn the AC off."""
        self._attr_hvac_mode = HVACMode.OFF
        await self._transmit()

    async def _transmit(self) -> None:
        """Encode the current state as an LG AC frame and send it via IR."""
        if self._attr_hvac_mode is HVACMode.OFF:
            command = LgAcCommand(mode=LgAcMode.OFF)
        else:
            lg_mode = HVAC_TO_LG[self._attr_hvac_mode]
            temperature = (
                int(self._attr_target_temperature)
                if lg_mode in TEMPERATURE_MODES
                else None
            )
            command = LgAcCommand(
                mode=lg_mode,
                temperature=temperature,
                fan=FAN_TO_LG.get(self._attr_fan_mode, LgAcFanSpeed.AUTO),
            )

        await async_send_command(self.hass, self._emitter_id, command)
        self.async_write_ha_state()

    async def _send_fixed(self, frame: int) -> None:
        """Transmit a stateless LG toggle frame (Jet Cool / swing) and update state."""
        await async_send_command(
            self.hass, self._emitter_id, LgAcFixedCommand(frame=frame)
        )
        self.async_write_ha_state()
