# ax-devil-mqtt

A Python package for working with Axis cameras MQTT functionality, with support for basic recording and replay functionality (over external MQTT broker).

## Important Disclaimer

This project is an independent, community-driven implementation and is **not** affiliated with or endorsed by Axis Communications AB. For official APIs and development resources, please refer to:
- [Axis Developer Community](https://www.axis.com/en-us/developer)

This library is provided "as is" without any guarantees regarding compatibility with future Axis firmware updates.


## Features

- Connect to Axis cameras and access their analytics streams
- Record analytics data for later analysis
- Replay previously recorded analytics sessions
- Flexible command-line interface
- Programmatic API for integration into other applications

## Installation

```bash
pip install -r requirements.txt
```

## Usage

This tool supports two main modes of operation:

### 1. Camera Mode

Working with live Axis cameras involves these steps:

1. List available analytics streams from your camera:
```bash
python src/ax_devil_mqtt/examples/cli.py camera list-streams \
    --camera-ip 192.168.1.200 \
    --username root \
    --password pass
```

2. Monitor specific analytics streams (optionally recording them):
```bash
# Monitor streams without recording
python src/ax_devil_mqtt/examples/cli.py camera monitor \
    --camera-ip 192.168.1.200 \
    --username root \
    --password pass \
    --broker 192.168.1.100 \
    --streams "com.axis.analytics_scene_description.v0.beta#1" \
    --streams "com.axis.object_analytics.v1"

# Monitor and record streams
python src/ax_devil_mqtt/examples/cli.py camera monitor \
    --camera-ip 192.168.1.200 \
    --username root \
    --password pass \
    --broker 192.168.1.100 \
    --streams "com.axis.analytics_scene_description.v0.beta#1" \
    --record
```

Options for `camera monitor`:
- `--camera-ip`: IP address of the Axis camera (required)
- `--username`: Camera username (required)
- `--password`: Camera password (required)
- `--broker, -b`: MQTT broker IP address or hostname (required)
- `--port, -p`: MQTT broker port (default: 1883)
- `--streams, -s`: Analytics streams to monitor (can be specified multiple times)
- `--record, -r`: Record messages to file
- `--duration, -d`: Monitoring duration in seconds (0 for infinite)

### 2. Simulation Mode

Replay previously recorded analytics data:

```bash
python src/ax_devil_mqtt/examples/cli.py simulation replay \
    recordings/camera_recording_20250216_132215.jsonl \
    --broker 192.168.1.100
```

Options for `simulation replay`:
- `--broker, -b`: MQTT broker IP address or hostname (required)
- `--port, -p`: MQTT broker port (default: 1883)

## MQTT Broker Configuration

This tool requires access to an MQTT broker where analytics data will be published. The broker can be:
- A dedicated MQTT broker server in your network (e.g., Mosquitto, HiveMQ)
- A cloud-based MQTT service
- A broker running on an edge device

You'll need the broker's IP address or hostname to connect. For example:
- Local network broker: `192.168.1.100`
- Cloud broker: `broker.hivemq.com`
- Edge device: `10.0.0.50`

## Programmatic Usage

The package can also be used programmatically in your Python applications:

### Camera Integration

```python
from ax_devil_mqtt.core.manager import MQTTStreamManager
from ax_devil_device_api import CameraConfig
from ax_devil_device_api.features.mqtt_client import BrokerConfig

# Configure camera
camera_config = CameraConfig.http(
    host="192.168.1.200",
    username="root",
    password="pass"
)

# Configure MQTT broker
broker_config = BrokerConfig(
    host="192.168.1.100",
    port=1883,
    use_tls=False,
    clean_session=True,
    auto_reconnect=True
)

# Create manager and specify analytics streams
manager = MQTTStreamManager(
    broker_config=broker_config,
    camera_config=camera_config,
    analytics_mqtt_data_source_key="com.axis.analytics_scene_description.v0.beta#1"
)

# Start monitoring and optionally record
manager.start()
manager.start_recording("recordings/camera_recording.jsonl")
```

### Replay Recorded Data

```python
from ax_devil_mqtt.core.manager import MQTTStreamManager, SimulatorConfig
from ax_devil_device_api.features.mqtt_client import BrokerConfig

# Configure replay
broker_config = BrokerConfig(
    host="192.168.1.100",
    port=1883,
    use_tls=False,
    clean_session=True,
    auto_reconnect=True
)
simulator_config = SimulatorConfig(
    recording_file="recordings/camera_recording.jsonl"
)

# Create manager for replay
manager = MQTTStreamManager(
    broker_config=broker_config,
    simulator_config=simulator_config,
    topics=[],  # Topics will be determined from the recording
    message_callback=lambda msg: print(f"Replaying: {msg}")
)

# Start replay
manager.start()
```

## File Format

Recordings are stored in JSONL (JSON Lines) format, with each line containing a JSON object with the following structure:

```json
{
    "timestamp": "2024-02-15T16:59:21.123456",
    "topic": "com.axis.analytics_scene_description.v0.beta#1",
    "payload": {
        // Analytics-specific payload
    }
}
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

