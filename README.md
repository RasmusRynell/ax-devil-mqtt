# ax-devil-mqtt

<div align="center">

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Type Hints](https://img.shields.io/badge/Type%20Hints-Strict-brightgreen.svg)](https://www.python.org/dev/peps/pep-0484/)

A Python package for working with Axis devices MQTT functionality, supporting analytics recording and replay over external MQTT brokers.

</div>

---

## 📋 Contents

- [Feature Overview](#-feature-overview)
- [Quick Start](#-quick-start)
- [Usage Examples](#-usage-examples)
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
      <td><b>🔌 Device Connection</b></td>
      <td>Connect to Axis devices and access their analytics streams</td>
      <td align="center"><code>MQTTStreamManager</code></td>
      <td align="center"><a href="#device-commands">ax-devil-mqtt device</a></td>
    </tr>
    <tr>
      <td><b>📊 Analytics Monitoring</b></td>
      <td>Monitor and process analytics data from devices</td>
      <td align="center"><code>AnalyticsMQTTConfig</code></td>
      <td align="center"><a href="#monitor-analytics">ax-devil-mqtt device monitor</a></td>
    </tr>
    <tr>
      <td><b>💾 Recording</b></td>
      <td>Record analytics data for later replay and analysis</td>
      <td align="center"><code>manager.record()</code></td>
      <td align="center"><a href="#recording-analytics">ax-devil-mqtt device monitor --record</a></td>
    </tr>
    <tr>
      <td><b>⏯️ Simulation/Replay</b></td>
      <td>Replay recorded analytics data for testing and development</td>
      <td align="center"><code>SimulationConfig</code></td>
      <td align="center"><a href="#replay-analytics">ax-devil-mqtt simulation replay</a></td>
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

<details open>
<summary><b>🔌 Device Connection and Analytics Monitoring</b></summary>
<p>

```python
import time
from ax_devil_mqtt import MQTTStreamManager, AnalyticsMQTTConfig
from ax_devil_device_api import DeviceConfig
from ax_devil_mqtt.core.types import BrokerConfig

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

def message_callback(message):
    print(message)

# Create analytics configuration
config = AnalyticsMQTTConfig(
    broker_config=broker_config,
    device_config=device_config,
    analytics_mqtt_data_source_key="com.axis.analytics_scene_description.v0.beta#1",
    message_callback=message_callback
)

manager = MQTTStreamManager(config)
manager.start()
time.sleep(10)
manager.stop()
```
</p>
</details>

<details>
<summary><b>⏯️ Simulation/Replay</b></summary>
<p>

```python
import time
from ax_devil_mqtt import MQTTStreamManager, SimulationConfig

def message_callback(message):
    print(message)

# Create simulation configuration
config = SimulationConfig(
    recording_file="recordings/device_recording.jsonl",
    message_callback=message_callback
)

# Create and start the manager
manager = MQTTStreamManager(config)
manager.start()
time.sleep(10)
manager.stop()
```
</p>
</details>

### CLI Usage Examples

<details open>
<summary><a name="device-commands"></a><b>🔌 Device Commands</b></summary>
<p>

```bash
# List available analytics streams
ax-devil-device-api-analytics-mqtt \
    --device-ip <device-ip> \
    --username <username> \
    --password <password> \
    sources
```
</p>
</details>

<details>
<summary><a name="monitor-analytics"></a><b>📊 Monitor Analytics Streams</b></summary>
<p>

```bash
# Monitor analytics streams
ax-devil-mqtt device monitor \
    --device-ip <device-ip> \
    --username <username> \
    --password <password> \
    --broker <broker-ip> \
    --port 1883 \
    --streams "com.axis.analytics_scene_description.v0.beta#1" \
    --duration 3600
```
</p>
</details>

<details>
<summary><a name="recording-analytics"></a><b>💾 Recording Analytics</b></summary>
<p>

```bash
# Monitor and record analytics streams
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
</p>
</details>

<details>
<summary><a name="replay-analytics"></a><b>⏯️ Replay Recorded Analytics</b></summary>
<p>

```bash
# Replay recorded analytics
ax-devil-mqtt simulation replay recordings/device_recording.jsonl
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

## ⚠️ Disclaimer

This project is an independent, community-driven implementation and is **not** affiliated with or endorsed by Axis Communications AB. For official APIs and development resources, please refer to [Axis Developer Community](https://www.axis.com/en-us/developer).

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.
