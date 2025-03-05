# ax-devil-mqtt

A Python package for working with Axis devices MQTT functionality, supporting analytics recording and replay over external MQTT brokers.

## Features

- Connect to Axis devices and access their analytics streams
- Record and replay analytics data
- Command-line interface and programmatic API
- Support for multiple analytics streams

## Quick Start

Requires Python ≥ 3.8 and (if not running in simulation mode) an MQTT broker (e.g., Mosquitto, HiveMQ).

### Environment Variables
For an easier experience, you can set the following environment variables:
```bash
export AX_DEVIL_TARGET_ADDR=<device-ip>
export AX_DEVIL_TARGET_USER=<username>
export AX_DEVIL_TARGET_PASS=<password>
export AX_DEVIL_USAGE_CLI="safe" # Set to "unsafe" to skip SSL certificate verification for CLI calls
```

### Example Usage

```python
from ax_devil_mqtt import MQTTStreamManager, AnalyticsMQTTConfig
from ax_devil_device_api import DeviceConfig
from ax_devil_device_api.features.mqtt_client import BrokerConfig

# Configure broker and device
broker_config = BrokerConfig(
    host="192.168.1.100",
    port=1883
)

device_config = DeviceConfig.http(
    host="192.168.1.200",
    username="root",
    password="pass"
)

# Create analytics configuration
config = AnalyticsMQTTConfig(
    broker_config=broker_config,
    device_config=device_config,
    analytics_mqtt_data_source_key="com.axis.analytics_scene_description.v0.beta#1"
)

# Create and start the manager
manager = MQTTStreamManager(config)
manager.start()
```

### Simulation/Replay Example

```python
from ax_devil_mqtt import MQTTStreamManager, SimulationConfig

# Create simulation configuration
config = SimulationConfig(
    recording_file="recordings/device_recording.jsonl"
)

# Create and start the manager
manager = MQTTStreamManager(config)
manager.start()
```

### CLI Usage Examples

The package provides a command-line interface for easy interaction with devices and analytics streams.

#### Device Commands

##### List Available Streams (using ax-devil-device-api)
```bash
ax-devil-device-api-analytics-mqtt \
    --device-ip <device-ip> \
    --username <username> \
    --password <password> \
    sources
```

##### Monitor Analytics Streams
```bash
ax-devil-mqtt device monitor \
    --device-ip <device-ip> \
    --username <username> \
    --password <password> \
    --broker <broker-ip> \
    --port 1883 \
    --streams "com.axis.analytics_scene_description.v0.beta#1" \
    --record \
    --duration 3600
```

#### Simulation Commands

##### Replay Recorded Analytics
```bash
ax-devil-mqtt simulation replay recordings/device_recording.jsonl
```

## Disclaimer

This project is an independent, community-driven implementation and is **not** affiliated with or endorsed by Axis Communications AB. For official APIs and development resources, please refer to [Axis Developer Community](https://www.axis.com/en-us/developer).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
