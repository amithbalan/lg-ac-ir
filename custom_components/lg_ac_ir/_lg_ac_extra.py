"""Fixed LG AC toggle codes not covered by the vendored state-frame encoder.

Jet Cool and vertical-swing are stateless *toggle* buttons on the LG remote: each
press sends a single fixed 28-bit frame, independent of the main cool/heat state
frame. They belong to the same LG2 code family as the power-off frame in
``_lg_ac.py`` (0x88 signature, low-nibble checksum) and are transmitted verbatim.

Frames captured from a real LG remote (model YAA1FB family) via an ESPHome IR
receiver and cross-checked against the encoder's checksum:
  - Jet Cool  : 0x880834F
  - Swing (V) : 0x8813149
"""

from __future__ import annotations

from typing import override

from infrared_protocols.commands import Command

from ._lg_ac import _encode_frame

# Stateless toggle frames (each transmit toggles the feature on the unit).
JET_COOL_FRAME = 0x880834F
SWING_VERTICAL_FRAME = 0x8813149


class LgAcFixedCommand(Command):
    """A stateless LG AC toggle code such as Jet Cool or vertical swing.

    Unlike ``LgAcCommand`` there is no mode/temperature/fan state - the frame is a
    fixed captured code sent as-is, using the same header/bit timings as the rest
    of the LG AC protocol.
    """

    frame: int

    def __init__(self, *, frame: int, modulation: int = 38000) -> None:
        """Initialise with the fixed 28-bit frame to transmit."""
        super().__init__(modulation=modulation)
        self.frame = frame

    @override
    def get_raw_timings(self) -> list[int]:
        """Encode the fixed frame with the standard LG AC bit timings."""
        return _encode_frame(self.frame)
