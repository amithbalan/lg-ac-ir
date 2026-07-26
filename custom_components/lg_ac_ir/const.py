"""Constants for the LG AC Infrared integration."""

from __future__ import annotations

DOMAIN = "lg_ac_ir"

# The `infrared` building-block integration's domain (emitters live here).
INFRARED_DOMAIN = "infrared"

# Config entry keys.
CONF_INFRARED_ENTITY_ID = "infrared_entity_id"

DEFAULT_NAME = "LG AC"

# LG AC IR protocol supports 16-30 C.
MIN_TEMP = 16
MAX_TEMP = 30
