"""
Tests for message processing functionality using the RawMqttClient without a real broker.
"""
import time
from typing import List

from ax_devil_mqtt.core.manager import AxisAnalyticsMqttClient, RawMqttClient
from ax_devil_mqtt.core.types import MqttMessage


class DummyMessage:
    def __init__(self, topic: str, payload: bytes, qos: int = 0, retain: bool = False):
        self.topic = topic
        self.payload = payload
        self.qos = qos
        self.retain = retain


class DummyClient:
    def __init__(self):
        self.on_connect = None
        self.on_message = None
        self.on_disconnect = None
        self.subscribed: List[str] = []
        self.unsubscribed: List[str] = []
        self.published = []
        self.username_pw: List[str] = []

    def connect(self, host, port):
        return 0

    def loop_start(self):
        return None

    def loop_stop(self):
        return None

    def disconnect(self):
        return None

    def subscribe(self, topic):
        self.subscribed.append(topic)
        return None

    def unsubscribe(self, topic):
        self.unsubscribed.append(topic)
        return None

    def publish(self, topic, payload, qos=0, retain=False):
        self.published.append((topic, payload, qos, retain))
        return None

    def username_pw_set(self, username, password=None):
        self.username_pw.append((username, password))


class DummyAnalyticsPublisher:
    def __init__(self, host: str | None = None):
        self.cleaned = False
        if host:
            self.client = type("PublisherClient", (), {"device_config": DummyDeviceConfig(host=host)})()

    def cleanup(self):
        self.cleaned = True


class DummyDeviceConfig:
    def __init__(self, host: str):
        self.host = host


def test_mqtt_client_dispatch_basic():
    processed_messages = []

    def callback(message: MqttMessage):
        processed_messages.append(message)

    dummy_client = DummyClient()
    mqtt_client = RawMqttClient(
        broker_host="broker",
        broker_port=1883,
        topics=["test/topic"],
        message_callback=callback,
        worker_threads=1,
        client=dummy_client,
    )

    mqtt_client._on_message(dummy_client, None, DummyMessage("test/topic", b"test_payload"))
    time.sleep(0.1)
    mqtt_client.stop()

    assert len(processed_messages) == 1
    assert processed_messages[0].payload == "test_payload"


def test_mqtt_client_sets_credentials_when_provided():
    dummy_client = DummyClient()

    RawMqttClient(
        broker_host="broker",
        broker_port=1883,
        topics=[],
        message_callback=lambda _: None,
        worker_threads=1,
        broker_username="user",
        broker_password="secret",
        client=dummy_client,
    )

    assert dummy_client.username_pw == [("user", "secret")]


def test_mqtt_client_dispatch_multiple():
    processed_messages = []

    def callback(message: MqttMessage):
        processed_messages.append(message)

    dummy_client = DummyClient()
    mqtt_client = RawMqttClient(
        broker_host="broker",
        broker_port=1883,
        topics=["test/topic"],
        message_callback=callback,
        worker_threads=2,
        client=dummy_client,
    )

    for i in range(5):
        mqtt_client._on_message(dummy_client, None, DummyMessage("test/topic", f"payload_{i}".encode()))

    time.sleep(0.2)
    mqtt_client.stop()

    assert len(processed_messages) == 5
    payloads = [msg.payload for msg in processed_messages]
    for i in range(5):
        assert f"payload_{i}" in payloads


def test_mqtt_client_error_handling():
    error_count = 0

    def error_callback(message: MqttMessage):
        nonlocal error_count
        error_count += 1
        raise ValueError("Test error")

    dummy_client = DummyClient()
    mqtt_client = RawMqttClient(
        broker_host="broker",
        broker_port=1883,
        topics=["test/topic"],
        message_callback=error_callback,
        worker_threads=1,
        client=dummy_client,
    )

    mqtt_client._on_message(dummy_client, None, DummyMessage("test/topic", b"test_payload"))
    time.sleep(0.1)
    mqtt_client.stop()

    assert error_count == 1


def test_analytics_client_with_injected_components():
    dummy_client = DummyClient()
    dummy_publisher = DummyAnalyticsPublisher()
    started = {"value": False, "stopped": False}

    class WrappedMqttClient(RawMqttClient):
        def start(self_inner):
            started["value"] = True

        def stop(self_inner):
            started["stopped"] = True

    analytics_client = AxisAnalyticsMqttClient(
        broker_host="broker",
        broker_port=1883,
        device_config=None,
        analytics_data_source_key="stream-key",
        message_callback=lambda _: None,
        worker_threads=1,
        create_publisher=False,
        mqtt_client=WrappedMqttClient(
            broker_host="broker",
            broker_port=1883,
            topics=["existing/topic"],
            message_callback=lambda _: None,
            worker_threads=1,
            client=dummy_client,
        ),
        publisher=dummy_publisher,
        topic="existing/topic",
    )

    analytics_client.start()
    analytics_client.stop()

    assert started["value"] is True
    assert started["stopped"] is True
    assert dummy_publisher.cleaned is True


def test_analytics_topic_hash_changes_with_device_ip():
    client_a = AxisAnalyticsMqttClient(
        broker_host="broker",
        broker_port=1883,
        device_config=DummyDeviceConfig(host="192.168.0.10"),
        analytics_data_source_key="stream-key",
        message_callback=lambda _: None,
        create_publisher=False,
    )
    client_b = AxisAnalyticsMqttClient(
        broker_host="broker",
        broker_port=1883,
        device_config=DummyDeviceConfig(host="192.168.0.11"),
        analytics_data_source_key="stream-key",
        message_callback=lambda _: None,
        create_publisher=False,
    )

    assert client_a.topic != client_b.topic


def test_analytics_topic_hash_is_stable_for_same_stream_and_device_ip():
    client_a = AxisAnalyticsMqttClient(
        broker_host="broker",
        broker_port=1883,
        device_config=DummyDeviceConfig(host="192.168.0.10"),
        analytics_data_source_key="stream-key",
        message_callback=lambda _: None,
        create_publisher=False,
    )
    client_b = AxisAnalyticsMqttClient(
        broker_host="broker",
        broker_port=1883,
        device_config=DummyDeviceConfig(host="192.168.0.10"),
        analytics_data_source_key="stream-key",
        message_callback=lambda _: None,
        create_publisher=False,
    )

    assert client_a.topic == client_b.topic


def test_analytics_topic_hash_uses_publisher_device_ip_when_device_config_missing():
    client_a = AxisAnalyticsMqttClient(
        broker_host="broker",
        broker_port=1883,
        device_config=None,
        analytics_data_source_key="stream-key",
        message_callback=lambda _: None,
        create_publisher=False,
        publisher=DummyAnalyticsPublisher(host="192.168.0.20"),
    )
    client_b = AxisAnalyticsMqttClient(
        broker_host="broker",
        broker_port=1883,
        device_config=None,
        analytics_data_source_key="stream-key",
        message_callback=lambda _: None,
        create_publisher=False,
        publisher=DummyAnalyticsPublisher(host="192.168.0.21"),
    )

    assert client_a.topic != client_b.topic
