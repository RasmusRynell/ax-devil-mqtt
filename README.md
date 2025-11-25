# ax-devil-mqtt

<div align="center">

Python package for easy configuration and consumption of an Axis devices analytics data over MQTT.

See also [ax-devil-device-api](https://github.com/rasmusrynell/ax-devil-device-api) and [ax-devil-rtsp](https://github.com/rasmusrynell/ax-devil-rtsp) for related tools.

</div>


---

## Install

```bash
pip install ax-devil-mqtt
```

## Configure (optional)

Set environment variables to avoid repeating credentials and broker details:

- `AX_DEVIL_TARGET_ADDR` – Device IP or hostname  
- `AX_DEVIL_TARGET_USER` – Device username  
- `AX_DEVIL_TARGET_PASS` – Device password  
- `AX_DEVIL_MQTT_BROKER_ADDR` – MQTT broker address  
- `AX_DEVIL_MQTT_BROKER_PASS` – MQTT broker password  

---

## CLI

Run `ax-devil-mqtt --help` or `ax-devil-mqtt help <command>` for full details. Common flows:

- Discover analytics data sources:

```bash
ax-devil-mqtt list-sources \
  --device-ip <device-ip> \
  --device-username <username> \
  --device-password <password>
```

- Monitor an analytics stream (use your IP instead of `localhost` for the broker):

```bash
ax-devil-mqtt monitor \
  --device-ip <device-ip> \
  --device-username <username> \
  --device-password <password> \
  --broker-address <broker-ip> \
  --broker-port 1883 \
  --stream "com.axis.analytics_scene_description.v0.beta#1" \
  --duration 3600       # 0 to run continuously
```

- Subscribe to an existing MQTT topic without configuring the device:

```bash
ax-devil-mqtt subscribe \
  --broker-address <broker-ip> \
  --broker-port 1883 \
  --topic "some/topic"
```

- Inspect or clean analytics publishers configured on the device:

```bash
ax-devil-mqtt list-publishers \
  --device-ip <device-ip> \
  --device-username <username> \
  --device-password <password>

ax-devil-mqtt clean \
  --device-ip <device-ip> \
  --device-username <username> \
  --device-password <password>
```

- Open the device’s Analytics MQTT API UI in your browser:

```bash
ax-devil-mqtt open-api \
  --device-ip <device-ip> \
  --device-username <username> \
  --device-password <password>
```

---

## Python API

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

---

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

pytest
mypy src tests
```

---

## Disclaimer

This project is an independent, community-driven implementation and is **not** affiliated with or endorsed by Axis Communications AB. For official APIs and development resources, see the [Axis Developer Community](https://www.axis.com/en-us/developer).

## License

MIT License - see [LICENSE](LICENSE) for details.
