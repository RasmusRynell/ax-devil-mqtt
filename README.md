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

### Basic Usage

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

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
