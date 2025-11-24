# ax-devil-mqtt

<div align="center">

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Type Hints](https://img.shields.io/badge/Type%20Hints-Strict-brightgreen.svg)](https://www.python.org/dev/peps/pep-0484/)

Python package for retrieving analytics data from Axis devices over MQTT.

See also: [ax-devil-device-api](https://github.com/rasmusrynell/ax-devil-device-api) for device API integration.

</div>

---

## 📋 Contents

- [Feature Overview](#-feature-overview)
- [Quick Start](#-quick-start)
- [Usage Examples](#-usage-examples)
- [Development](#-development)
- [Disclaimer](#-disclaimer)
- [License](#-license)

---

## 🔍 Feature Overview

<table>
  <thead>
    <tr>
      <th>Feature</th>
      <th>Description</th>
      <th align="center">Python API</th>
      <th align="center">CLI Tool</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><b>🔌 Device Setup</b></td>
      <td>Configure Axis devices for analytics MQTT publishing</td>
      <td align="center"><code>RawMQTTManager</code></td>
      <td align="center"><a href="#mqtt-connection">ax-devil-mqtt device monitor</a></td>
    </tr>
    <tr>
      <td><b>📊 Analytics Streaming</b></td>
      <td>Stream analytics data from Axis devices with automated setup</td>
      <td align="center"><code>AnalyticsManager</code></td>
      <td align="center"><a href="#analytics-streaming">ax-devil-mqtt device monitor</a></td>
    </tr>
    <tr>
      <td><b>💾 Data Recording</b></td>
      <td>Record analytics MQTT data for later replay and analysis</td>
      <td align="center"><code>manager.start(recording_file)</code></td>
      <td align="center"><a href="#data-recording">ax-devil-mqtt device monitor --record</a></td>
    </tr>
    <tr>
      <td><b>⏯️ Replay</b></td>
      <td>Replay recorded MQTT data for testing and development</td>
      <td align="center"><code>ReplayManager</code></td>
      <td align="center"><a href="#data-replay">ax-devil-mqtt replay</a></td>
    </tr>
  </tbody>
</table>

---

## 🚀 Quick Start

### Installation

```bash
pip install ax-devil-mqtt
```

### Environment Variables
For an easier experience, you can set the following environment variables:
```bash
export AX_DEVIL_TARGET_ADDR=<device-ip>
export AX_DEVIL_TARGET_USER=<username>
export AX_DEVIL_TARGET_PASS=<password>
export AX_DEVIL_USAGE_CLI="safe" # Set to "unsafe" to skip SSL certificate verification for CLI calls
```

---

## 💻 Usage Examples

### Python API Usage

🔌 MQTT Connection and Analytics Streaming

```python
import time
from ax_devil_mqtt import AnalyticsManager
from ax_devil_mqtt.core.types import Message
from ax_devil_device_api import DeviceConfig

# Configure device
device_config = DeviceConfig.http(
    host="192.168.1.200",
    username="root",
    password="pass"
)

def message_callback(message: Message):
    print(f"Topic: {message.topic}")
    print(f"Payload: {message.payload}")
    print(f"Timestamp: {message.timestamp}")

# Create analytics manager
manager = AnalyticsManager(
    broker_host="192.168.1.100",
    broker_port=1883,
    device_config=device_config,
    analytics_data_source_key="com.axis.analytics_scene_description.v0.beta#1",
    message_callback=message_callback
)

manager.start()
# or manager.start(recording_file="recordings/some_file_name.jsonl")
time.sleep(10)
manager.stop()
```

⏯️ Replay

```python
import time
from ax_devil_mqtt import ReplayManager
from ax_devil_mqtt.core.types import Message, ReplayStats

def message_callback(message: Message):
    print(f"Topic: {message.topic}")
    print(f"Payload: {message.payload}")
    print(f"Timestamp: {message.timestamp}")

def on_replay_complete(stats: ReplayStats):
    print(f"Replay completed!")
    print(f"  Total messages: {stats.message_count}")
    print(f"  Average drift: {stats.avg_drift:.2f}ms")
    print(f"  Max drift: {stats.max_drift:.2f}ms")

# Create a replay manager
manager = ReplayManager(
    recording_file="recordings/device_recording.jsonl",
    message_callback=message_callback,
    on_replay_complete=on_replay_complete
)

# Start the manager
manager.start()
time.sleep(10)
manager.stop()
```

### CLI Usage Examples

<details open>
<summary><b>🔍 Discover Available Analytics Streams</b></summary>
<p>

Using ax-devil-device-api:
```bash
ax-devil-device-api-analytics-mqtt sources
```

Or discover and list with ax-devil-mqtt:
```bash
ax-devil-mqtt device list-sources --device-ip <device-ip> --username <username> --password <password>
```
</p>
</details>

<details open>
<summary><a name="mqtt-connection"></a><a name="analytics-streaming"></a><b>📊 Streaming Analytics Data Source</b></summary>
<p>

```bash
ax-devil-mqtt device monitor \
    --device-ip <device-ip> \
    --username <username> \
    --password <password> \
    --broker <broker-ip> \
    --port 1883 \
    --stream "com.axis.analytics_scene_description.v0.beta#1" \
    --duration 3600
```
</p>
</details>

<details>
<summary><a name="data-recording"></a><b>💾 Recording MQTT Data</b></summary>
<p>

```bash
ax-devil-mqtt device monitor \
    --device-ip <device-ip> \
    --username <username> \
    --password <password> \
    --broker <broker-ip> \
    --port 1883 \
    --stream "com.axis.analytics_scene_description.v0.beta#1" \
    --record \
    --duration 3600
```
</p>
</details>

<details>
<summary><a name="data-replay"></a><b>⏯️ Replaying Recorded Data</b></summary>
<p>

```bash
ax-devil-mqtt replay recordings/device_recording.jsonl
```
</p>
</details>

### Example Scripts

<details>
<summary><b>Analytics Monitor Example</b></summary>
<p>

```bash
python src/ax_devil_mqtt/examples/analytics_monitor.py --host <broker-ip>
```
</p>
</details>

<details>
<summary><b>Replay Example</b></summary>
<p>

```bash
python src/ax_devil_mqtt/examples/replay.py recordings/device_recording.jsonl
```
</p>
</details>

> **Note:** For more examples, check the [examples directory](src/ax_devil_mqtt/examples) in the source code.

---

## 🛠️ Development

Development dependencies are defined in `pyproject.toml` under the `dev` optional extras.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run the checks:
```bash
pytest
mypy src tests
```

---

## ⚠️ Disclaimer

This project is an independent, community-driven implementation and is **not** affiliated with or endorsed by Axis Communications AB. For official APIs and development resources, please refer to [Axis Developer Community](https://www.axis.com/en-us/developer).

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.
