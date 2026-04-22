# ax-devil-mqtt Python API Reference

**Install**: `pip install ax-devil-mqtt` (or `uv pip install ax-devil-mqtt`)
**Depends on**: `ax-devil-device-api`, `paho-mqtt`

Public exports from `ax_devil_mqtt`:

- `RawMqttClient` — Low-level MQTT client with threaded callbacks
- `AxisAnalyticsMqttClient` — High-level client that auto-configures device analytics publishing
- `TemporaryAnalyticsMQTTPublisher` — Manages temporary publisher lifecycle on device
- `MqttMessage` — Dataclass for received messages

## MqttMessage

```python
@dataclass
class MqttMessage:
    topic: str      # MQTT topic string
    payload: str    # Decoded UTF-8 payload
    qos: int = 0
    retain: bool = False

    def to_dict(self) -> dict  # Returns {"topic", "payload", "qos", "retain"}
```

## RawMqttClient

Connects to an MQTT broker and dispatches messages to a callback on a thread pool.

```python
from ax_devil_mqtt import RawMqttClient, MqttMessage

client = RawMqttClient(
    broker_host="<broker-ip>",   # Required
    broker_port=1883,               # Required
    topics=["some/topic"],          # List of topics to subscribe to (or None)
    message_callback=lambda msg: print(msg.payload),  # Required: Callable[[MqttMessage], None]
    worker_threads=1,               # Thread pool size for callback dispatch
    connection_timeout_seconds=5,   # Seconds to wait for connection
    broker_username="",             # Optional
    broker_password="",             # Optional
)
client.start()     # Connects and starts network loop. Raises ConnectionError on failure.
client.subscribe("another/topic")   # Subscribe to additional topic after start
client.unsubscribe("some/topic")    # Unsubscribe
client.publish("out/topic", '{"key": "value"}')  # Publish a message
client.is_connected()               # Returns bool
client.stop()      # Disconnects, shuts down thread pool
```

Key behaviors:
- `start()` blocks until connected or `connection_timeout_seconds` elapses.
- `start()` raises `ConnectionError` on failure.
- Callbacks are dispatched on the thread pool, not the MQTT network thread.
- `stop()` is idempotent.

## AxisAnalyticsMqttClient

Configures an Axis device to publish analytics data to a broker, then subscribes. Cleans up the temporary publisher on stop.

```python
from ax_devil_mqtt import AxisAnalyticsMqttClient, MqttMessage
from ax_devil_device_api import DeviceConfig

device_config = DeviceConfig.http(host="<device-ip>", username="<user>", password="<pass>")

client = AxisAnalyticsMqttClient(
    broker_host="<broker-ip>",     # Required: must be reachable from the device
    broker_port=1883,                 # Required
    device_config=device_config,      # Required when create_publisher=True
    analytics_data_source_key="com.axis.analytics_scene_description.v0.beta#1",  # Required
    message_callback=lambda msg: print(msg.payload),  # Required
    worker_threads=1,                 # Optional
    broker_username="",               # Optional
    broker_password="",               # Optional
    topic=None,                       # Optional: override auto-generated topic
    client_id=None,                   # Optional: MQTT client ID
    create_publisher=True,            # Set False to skip device configuration
)
client.start()   # Connects to broker (publisher already created in __init__)
client.stop()    # Disconnects and cleans up temporary publisher on device
```

Key behaviors:
- Constructor creates the temporary publisher on the device immediately (not deferred to `start()`).
- Auto-generated topic: `ax-devil/temp/<sha256(source_key:device_host)[:8]>`.
- `stop()` calls `TemporaryAnalyticsMQTTPublisher.cleanup()` which restores original device MQTT state.
- If `create_publisher=False`, no device interaction occurs — provide a `topic` to subscribe to an existing publisher.
- The `topic` attribute holds the actual topic being used.

## TemporaryAnalyticsMQTTPublisher

Low-level class managing the device-side publisher lifecycle. Usually used via `AxisAnalyticsMqttClient`, not directly.

```python
from ax_devil_mqtt import TemporaryAnalyticsMQTTPublisher
from ax_devil_device_api import DeviceConfig

publisher = TemporaryAnalyticsMQTTPublisher(
    device_config=DeviceConfig.http(host="<device-ip>", username="<user>", password="<pass>"),
    broker_host="<broker-ip>",
    broker_port=1883,
    topic="ax-devil/temp/abc123",
    client_id="ax-devil/temp/abc123",
    analytics_data_source_key="com.axis.analytics_scene_description.v0.beta#1",
)
# Publisher is now active on the device.
publisher.cleanup()  # Removes publisher and restores original MQTT config on device.
```

Key behaviors:
- Constructor saves original device MQTT state, configures broker, creates publisher, activates MQTT.
- `cleanup()` restores original MQTT state (config + active/inactive). Idempotent.
- Reuses existing publisher if one matches topic + source key + qos=0 + retain=False + no topic prefix.

## Typical Python Workflows

### Collect analytics data from a device

```python
import json
from ax_devil_mqtt import AxisAnalyticsMqttClient, MqttMessage
from ax_devil_device_api import DeviceConfig

frames = []

def on_message(msg: MqttMessage) -> None:
    data = json.loads(msg.payload)
    frames.append(data)

device = DeviceConfig.http(host="<device-ip>", username="<user>", password="<pass>")
client = AxisAnalyticsMqttClient(
    broker_host="<broker-ip>",
    broker_port=1883,
    device_config=device,
    analytics_data_source_key="com.axis.analytics_scene_description.v0.beta#1",
    message_callback=on_message,
)
client.start()
# ... collect data ...
client.stop()
```

### Subscribe to arbitrary MQTT topic (no device needed)

```python
from ax_devil_mqtt import RawMqttClient

client = RawMqttClient(
    broker_host="<broker-ip>",
    broker_port=1883,
    topics=["my/topic/#"],
    message_callback=lambda msg: print(f"{msg.topic}: {msg.payload}"),
)
client.start()
```
