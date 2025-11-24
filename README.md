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
      <td align="center"><code>AxisAnalyticsMqttClient</code></td>
      <td align="center"><a href="#mqtt-connection">ax-devil-mqtt device monitor</a></td>
    </tr>
    <tr>
      <td><b>📊 Analytics Streaming</b></td>
      <td>Stream analytics data from Axis devices with automated setup</td>
      <td align="center"><code>AxisAnalyticsMqttClient</code></td>
      <td align="center"><a href="#analytics-streaming">ax-devil-mqtt device monitor</a></td>
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
from ax_devil_mqtt import AxisAnalyticsMqttClient, RawMqttClient, MqttMessage
from ax_devil_device_api import DeviceConfig

# Subscribe to an existing topic
client = RawMqttClient(
    broker_host="192.168.1.100",
    broker_port=1883,
    topics=["some/topic"],
    message_callback=lambda message: print(message.payload),
    worker_threads=1,  # dispatch callbacks on a background thread
)
client.start()
time.sleep(5)
client.stop()

# Or configure the device to publish analytics and subscribe automatically
device_config = DeviceConfig.http(host="192.168.1.200", username="root", password="pass")

analytics_client = AxisAnalyticsMqttClient(
    broker_host="192.168.1.100",
    broker_port=1883,
    device_config=device_config,
    analytics_data_source_key="com.axis.analytics_scene_description.v0.beta#1",
    message_callback=lambda message: print(message.payload),
    worker_threads=1,
)
analytics_client.start()
time.sleep(5)
analytics_client.stop()
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
