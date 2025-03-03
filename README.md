# ax-devil-mqtt

A Python package for working with Axis devices MQTT functionality, supporting analytics recording and replay over external MQTT brokers.

## Important Disclaimer

This project is an independent, community-driven implementation and is **not** affiliated with or endorsed by Axis Communications AB. For official APIs and development resources, please refer to [Axis Developer Community](https://www.axis.com/en-us/developer).

## Features

- Connect to Axis devices and access their analytics streams
- Record and replay analytics data
- Command-line interface and programmatic API
- Support for multiple analytics streams

## Quick Start

### Installation

```bash
pip install .
```

Requires Python ≥ 3.8 and an MQTT broker (e.g., Mosquitto, HiveMQ).

### Environment Variables
For an easier experience, you can set the following environment variables:
```bash
export AX_DEVIL_TARGET_ADDR=<device-ip>
export AX_DEVIL_TARGET_USER=<username>
export AX_DEVIL_TARGET_PASS=<password>
```

### Example Usage

```python
from ax_devil_mqtt.core.manager import MQTTStreamManager
from ax_devil_device_api import DeviceConfig
from ax_devil_device_api.features.mqtt_client import BrokerConfig

# Configure and start monitoring
manager = MQTTStreamManager(
    broker_config=BrokerConfig(host="192.168.1.100"),
    device_config=DeviceConfig.http(
        host="192.168.1.200",
        username="root",
        password="pass"
    ),
    analytics_mqtt_data_source_key="com.axis.analytics_scene_description.v0.beta#1"
)

manager.start()
```

### CLI Usage Examples

The package provides a command-line interface for easy interaction with devices and analytics streams.

#### Device Commands

##### List Available Streams (using ax-devil-device-api)
```bash
ax-devil-device-api-analytics-mqtt \
    --device-ip 192.168.1.81 \
    --username root \
    --password fusion \
    sources
```

##### Monitor Analytics Streams
```bash
ax-devil-mqtt device monitor \
    --device-ip 192.168.1.200 \
    --username root \
    --password pass \
    --broker localhost \
    --port 1883 \
    --streams "com.axis.analytics_scene_description.v0.beta#1" \
    --record \
    --duration 3600
```

#### Simulation Commands

##### Replay Recorded Analytics
```bash
ax-devil-mqtt simulation replay recordings/device_recording.jsonl \
    --broker localhost \
    --port 1883
```


### Example Scripts

The package includes example scripts demonstrating key functionality:

#### Recording Analytics Data
```bash
python src/ax_devil_mqtt/examples/analytics_monitor.py \
    --host <broker_ip> \
    --port 1883 \
    --duration 10
```

This script connects to an Axis device and records MQTT analytics data for a specified duration. It requires the following environment variables:
- `AX_DEVIL_TARGET_ADDR`: IP address of the target device
- `AX_DEVIL_TARGET_USER`: Device username
- `AX_DEVIL_TARGET_PASS`: Device password

Options:
- `--host`: MQTT broker host IP (required)
- `--port`: MQTT broker port (default: 1883)
- `--duration`: Recording duration in seconds (default: 10)

Recordings are saved to the `recordings` directory with timestamps in the filename.

#### Replaying Recorded Data
```bash
python src/ax_devil_mqtt/examples/replay.py \
    --host <broker_ip> \
    recordings/mqtt_recording_20240321_123456.jsonl
```

This script replays previously recorded MQTT messages through an MQTT broker. It's useful for testing and development without requiring a physical device.

Options:
- `--host`: MQTT broker host IP (required)
- `--port`: MQTT broker port (default: 1883)
- `recording_path`: Path to the recording file (required)

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
