# LG AC Infrared

A Home Assistant custom integration that exposes an **LG air conditioner as a native `climate` entity**, transmitting over Home Assistant's [`infrared`](https://www.home-assistant.io/integrations/infrared/) building-block platform.

It is the **air-conditioner counterpart to the built-in [`lg_infrared`](https://www.home-assistant.io/integrations/lg_infrared/) integration**, which currently only supports TVs. The LG AC IR protocol encoding is provided upstream by [`infrared-protocols`](https://github.com/home-assistant-libs/infrared-protocols) (`commands/lg_ac.py`) — this integration is the thin mapping layer that turns Home Assistant climate commands into those IR frames.

## Why this exists

Home Assistant 2026.4 introduced the `infrared` platform: emitter integrations (ESPHome, Broadlink…) expose infrared entities, and *consumer* integrations send device commands through them. The only official consumers so far — `lg_infrared` and `samsung_infrared` — are **TV-only**. There is no consumer that turns an infrared emitter into an **AC**. This fills that gap for LG.

## Requirements

- Home Assistant **2026.4** or newer (for the `infrared` platform).
- A working **infrared emitter entity**. The easiest is an **ESPHome** device running the [`ir_rf_proxy`](https://esphome.io/components/ir_rf_proxy/) component with a `remote_transmitter` wired to an IR LED (a plain IR blaster — *not* a Tuya "TuyaMCU" blaster whose IR sits behind a co-processor).

## Installation (HACS)

1. HACS → ⋮ → **Custom repositories**.
2. Add `https://github.com/amithbalan/lg-ac-ir` with category **Integration**.
3. Install **LG AC Infrared**, then restart Home Assistant.
4. **Settings → Devices & services → Add Integration → LG AC Infrared**.
5. Pick your infrared **emitter** and give the AC a name.

## Features

| Capability | Supported |
|---|---|
| HVAC modes | off, cool, heat, dry, fan_only |
| Target temperature | 16–30 °C (cool/heat) |
| Fan speed | quiet, low, medium, high, auto |
| Power on/off | ✅ |

**Notes**
- IR is one-way, so the entity is **assumed-state** — Home Assistant tracks the last commanded state; it cannot read the AC back. If you change the AC with its handheld remote, HA won't know.
- **Swing** is not exposed by the current `infrared-protocols` LG AC encoder, so it's omitted here. It can be added when upstream supports it.

## How it works

```
climate command  ─▶  LgAcCommand(mode, temperature, fan)   # infrared_protocols
                 ─▶  async_send_command(hass, emitter_id, command)   # infrared platform
                 ─▶  ESPHome ir_rf_proxy emitter  ─▶  IR LED  ─▶  your LG AC
```

## Credits & third-party code

- IR protocol encoding: [home-assistant-libs/infrared-protocols](https://github.com/home-assistant-libs/infrared-protocols).
  The LG AC encoder (`custom_components/lg_ac_ir/_lg_ac.py`) is **vendored** from that
  project (MIT License, © Home Assistant Team) so the integration also works on Home
  Assistant versions whose bundled `infrared-protocols` predates the LG AC encoder
  (e.g. HA 2026.7.x ships 6.3.0). Only the `Command` import was repointed; encoder logic is
  unchanged. It still uses the platform's `Command` base class and `async_send_command` API.
- Built on the Home Assistant `infrared` platform.

## License

MIT — see [LICENSE](LICENSE).
