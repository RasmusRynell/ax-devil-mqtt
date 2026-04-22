---
name: ax-devil-mqtt
description: 'Use the ax-devil-mqtt package (CLI and Python API) to discover, configure, and consume analytics MQTT data from Axis cameras. Use when asked to "list sources", "monitor analytics", "subscribe MQTT", "clean publishers", "open API", connect to an Axis camera over MQTT, stream analytics data, set up an MQTT publisher, or write code using AxisAnalyticsMqttClient or RawMqttClient.'
---

# ax-devil-mqtt

Python package for configuring Axis devices to publish analytics data over MQTT and consuming that data via CLI or Python API.

**Package**: `ax-devil-mqtt` (PyPI)
**Depends on**: `ax-devil-device-api`, `paho-mqtt`, `click`

## Prerequisites — MUST do before any command

1. **Ensure the CLI is installed.** Run `which ax-devil-mqtt`. If not found, install it:
   ```bash
   uv tool install ax-devil-mqtt
   ```
2. **Resolve credentials.** Before running any command or writing code that talks to a device or broker, you MUST have concrete values for the required parameters. Follow this procedure:
   - Check env vars: `echo $AX_DEVIL_TARGET_ADDR $AX_DEVIL_TARGET_USER $AX_DEVIL_TARGET_PASS $AX_DEVIL_MQTT_BROKER_ADDR`
   - If any required value is missing or empty, **ASK the user** — do NOT guess or use placeholder IPs.
   - Commands that only talk to the broker (`subscribe`) need broker address/port only.
   - Commands that talk to a device (`list-sources`, `monitor`, `list-publishers`, `clean`, `open-api`) need device IP, username, and password.
   - `monitor` needs both device credentials AND broker address.

## References

Load only the reference you need:

- **[CLI Reference](./references/cli.md)** — All commands, flags, env vars, and CLI workflows
- **[Python API Reference](./references/python-api.md)** — `RawMqttClient`, `AxisAnalyticsMqttClient`, `TemporaryAnalyticsMQTTPublisher`, `MqttMessage`, and Python workflows

## Environment Variables

The CLI reads these when the corresponding flag is not supplied:

| Variable | CLI flag fallback |
|----------|-------------------|
| `AX_DEVIL_TARGET_ADDR` | `--device-ip` / `-a` |
| `AX_DEVIL_TARGET_USER` | `--device-username` / `-u` |
| `AX_DEVIL_TARGET_PASS` | `--device-password` / `-p` |
| `AX_DEVIL_MQTT_BROKER_ADDR` | `--broker-address` / `-b` |
| `AX_DEVIL_MQTT_BROKER_PASS` | `--broker-password` / `-W` |

## Quick Decision Guide

| Task | Tool | Reference |
|------|------|-----------|
| Discover analytics sources on a device | `ax-devil-mqtt list-sources` | [CLI](./references/cli.md) |
| Stream analytics to terminal | `ax-devil-mqtt monitor` | [CLI](./references/cli.md) |
| Subscribe to raw MQTT topic | `ax-devil-mqtt subscribe` or `RawMqttClient` | [CLI](./references/cli.md) / [Python](./references/python-api.md) |
| Collect analytics in Python | `AxisAnalyticsMqttClient` | [Python](./references/python-api.md) |
| Low-level MQTT pub/sub in Python | `RawMqttClient` | [Python](./references/python-api.md) |
| Inspect device publishers | `ax-devil-mqtt list-publishers` | [CLI](./references/cli.md) |
| Clean up temp publishers | `ax-devil-mqtt clean` | [CLI](./references/cli.md) |
| Open device API UI | `ax-devil-mqtt open-api` | [CLI](./references/cli.md) |

## Key Concepts

- **Temporary publishers**: `monitor` and `AxisAnalyticsMqttClient` create a temporary MQTT publisher on the device (topic prefix `ax-devil/temp/`). It is cleaned up automatically on exit, or manually via `ax-devil-mqtt clean`.
- **Broker address**: Must be reachable from the camera — never use `localhost`.
- **Analytics source key**: Discover with `list-sources`. Common value: `com.axis.analytics_scene_description.v0.beta#1`.
- **Callbacks**: Both Python clients dispatch `MqttMessage` to your callback on a thread pool (not the MQTT network thread).
