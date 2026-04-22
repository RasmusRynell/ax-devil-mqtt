# ax-devil-mqtt CLI Reference

Entry point: `ax-devil-mqtt`.

**Install** (if `which ax-devil-mqtt` returns nothing):
```bash
uv tool install ax-devil-mqtt
```

## Environment Variables

The CLI reads these when the corresponding flag is not supplied:

| Variable | CLI flag fallback |
|----------|-------------------|
| `AX_DEVIL_TARGET_ADDR` | `--device-ip` / `-a` |
| `AX_DEVIL_TARGET_USER` | `--device-username` / `-u` |
| `AX_DEVIL_TARGET_PASS` | `--device-password` / `-p` |
| `AX_DEVIL_MQTT_BROKER_ADDR` | `--broker-address` / `-b` |
| `AX_DEVIL_MQTT_BROKER_PASS` | `--broker-password` / `-W` |

## Common Options

| Flag | Short | Env var | Description |
|------|-------|---------|-------------|
| `--device-ip` | `-a` | `AX_DEVIL_TARGET_ADDR` | Device IP or hostname |
| `--device-username` | `-u` | `AX_DEVIL_TARGET_USER` | Device username |
| `--device-password` | `-p` | `AX_DEVIL_TARGET_PASS` | Device password |
| `--broker-address` | `-b` | `AX_DEVIL_MQTT_BROKER_ADDR` | MQTT broker address |
| `--broker-port` | `-P` | — | Broker port (default: 1883) |
| `--broker-username` | `-U` | — | Broker username |
| `--broker-password` | `-W` | `AX_DEVIL_MQTT_BROKER_PASS` | Broker password |

## Commands

### `list-sources` — Discover available analytics data sources on a device

```bash
ax-devil-mqtt list-sources \
  --device-ip <ip> --device-username <user> --device-password <pass>
```

Output: one line per source, e.g. `com.axis.analytics_scene_description.v0.beta#1`.

### `monitor` — Configure device to publish analytics and subscribe

```bash
ax-devil-mqtt monitor \
  --device-ip <ip> --device-username <user> --device-password <pass> \
  --broker-address <broker-ip> --broker-port 1883 \
  --stream "com.axis.analytics_scene_description.v0.beta#1" \
  --duration 3600
```

- `--broker-address` must NOT be `localhost` — the camera connects to it, so use a reachable IP.
- `--duration 0` runs until Ctrl-C.
- Creates a temporary publisher on the device, subscribes, and cleans up on exit.

### `subscribe` — Subscribe to a raw MQTT topic (no device configuration)

```bash
ax-devil-mqtt subscribe \
  --broker-address <broker-ip> --broker-port 1883 \
  --topic "some/topic"
```

Does not interact with any Axis device. Connects directly to the broker and prints messages.

### `list-publishers` — Show existing analytics MQTT publishers on a device

```bash
ax-devil-mqtt list-publishers \
  --device-ip <ip> --device-username <user> --device-password <pass>
```

Output: id, topic, and data_source_key per publisher.

### `clean` — Remove temporary publishers created by ax-devil-mqtt

```bash
ax-devil-mqtt clean \
  --device-ip <ip> --device-username <user> --device-password <pass>
```

Deletes only publishers whose topic starts with `ax-devil/temp/`.

### `open-api` — Open the Analytics MQTT API UI in a browser

```bash
ax-devil-mqtt open-api \
  --device-ip <ip> --device-username <user> --device-password <pass>
```

### `version` — Print installed version

```bash
ax-devil-mqtt version
```

### `help` — Show help for a command

```bash
ax-devil-mqtt help <command>
```

## Typical CLI Workflows

### Discover what analytics a device offers

```bash
ax-devil-mqtt list-sources --device-ip <ip> -u <user> -p <pass>
```

### Stream analytics data to terminal

```bash
ax-devil-mqtt monitor \
  --device-ip <ip> -u <user> -p <pass> \
  --broker-address <broker-ip> --stream "com.axis.analytics_scene_description.v0.beta#1"
```

### Clean up stale temporary publishers

```bash
ax-devil-mqtt clean --device-ip <ip> -u <user> -p <pass>
```
