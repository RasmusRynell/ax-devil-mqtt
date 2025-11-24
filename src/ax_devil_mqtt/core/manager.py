import hashlib
import json
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

import paho.mqtt.client as mqtt
from ax_devil_device_api import DeviceConfig

from .temporary_analytics_mqtt_publisher import TemporaryAnalyticsMQTTPublisher
from .types import MessageCallback, MqttMessage

logger = logging.getLogger(__name__)


class RawMqttClient:
    """Minimal wrapper around paho-mqtt with optional threaded callbacks."""

    def __init__(
        self,
        broker_host: str,
        broker_port: int,
        topics: Optional[List[str]],
        message_callback: MessageCallback,
        worker_threads: int = 1,
        connection_timeout_seconds: int = 5,
        client: Optional[mqtt.Client] = None,
    ):
        if worker_threads < 1:
            raise ValueError("worker_threads must be at least 1")

        self._broker_host = broker_host
        self._broker_port = broker_port
        self._topics = list(topics or [])
        self._message_callback = message_callback
        self._connection_timeout_seconds = connection_timeout_seconds
        self._connected = False
        self._connection_error: Optional[str] = None
        self._stop_event = threading.Event()

        self._executor = ThreadPoolExecutor(max_workers=worker_threads)

        self._client = client or mqtt.Client()
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect

    def start(self) -> None:
        """Connect to the broker and start the network loop."""
        self._connection_error = None
        if not self._connected:
            logger.info(f"Connecting to MQTT broker at {self._broker_host}:{self._broker_port}")
            try:
                self._client.connect(self._broker_host, self._broker_port)
            except Exception as e:
                logger.error(f"Error connecting to MQTT broker: {e}")
                raise ConnectionError(f"Failed to connect to MQTT broker: {e}") from e

        self._client.loop_start()

        start_time = time.time()
        while not self._connected and time.time() - start_time < self._connection_timeout_seconds:
            if self._connection_error:
                self._client.loop_stop()
                raise ConnectionError(self._connection_error)
            time.sleep(0.1)

        if not self._connected:
            self._client.loop_stop()
            raise ConnectionError("Timed out waiting for MQTT connection")

    def stop(self) -> None:
        """Stop the network loop and shut down the worker pool."""
        if self._stop_event.is_set():
            return

        self._stop_event.set()

        try:
            self._client.loop_stop()
            self._client.disconnect()
        except Exception as e:
            logger.warning(f"Error while stopping MQTT client: {e}")
        finally:
            try:
                self._executor.shutdown(wait=True)
            except Exception as e:
                logger.warning(f"Error during executor shutdown: {e}")
            self._connected = False

    def subscribe(self, topic: str) -> None:
        """Subscribe to an additional topic."""
        if topic not in self._topics:
            self._topics.append(topic)
        if self._connected:
            self._client.subscribe(topic)

    def unsubscribe(self, topic: str) -> None:
        """Unsubscribe from a topic."""
        if topic in self._topics:
            self._topics.remove(topic)
        if self._connected:
            self._client.unsubscribe(topic)

    def publish(self, topic: str, payload, qos: int = 0, retain: bool = False):
        """Publish a message."""
        return self._client.publish(topic, payload=payload, qos=qos, retain=retain)

    def is_connected(self) -> bool:
        """Check connection state."""
        return self._connected

    # Internal callbacks -------------------------------------------------
    def _on_connect(self, client, userdata, flags, rc):
        """Internal callback when connection is established."""
        if rc == 0:
            self._connected = True
            for topic in self._topics:
                self._client.subscribe(topic)
        else:
            self._connected = False
            self._connection_error = f"Failed to connect to MQTT broker with code {rc}"
            logger.error(self._connection_error)

    def _on_message(self, client, userdata, message):
        """Internal callback for handling incoming messages."""
        try:
            payload_str = message.payload.decode()
            try:
                payload = json.loads(payload_str)
            except json.JSONDecodeError:
                payload = payload_str

            mqtt_message = MqttMessage(
                topic=message.topic,
                payload=payload,
                qos=message.qos,
                retain=message.retain,
            )
            self._dispatch_message(mqtt_message)
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def _on_disconnect(self, client, userdata, rc):
        """Internal callback when disconnected."""
        self._connected = False
        if rc != 0:
            logger.error(f"Unexpected disconnection (code {rc})")

    def _dispatch_message(self, message: MqttMessage) -> None:
        """Send a message to the worker pool for processing."""
        try:
            self._executor.submit(self._safe_invoke_callback, message)
        except RuntimeError:
            logger.warning("Executor is shutting down, message dropped")

    def _safe_invoke_callback(self, message: MqttMessage) -> None:
        """Invoke the user callback and catch/log errors."""
        try:
            self._message_callback(message)
        except Exception as e:
            logger.error(
                f"Error in message callback: {str(e)}. "
                f"Message topic: {message.topic}, "
                f"Message size: {len(str(message))} bytes"
            )


class AxisAnalyticsMqttClient:
    """Helper that sets up a temporary analytics publisher and subscribes to it."""

    def __init__(
        self,
        broker_host: str,
        broker_port: int,
        device_config: Optional[DeviceConfig],
        analytics_data_source_key: str,
        message_callback: MessageCallback,
        worker_threads: int = 1,
        broker_username: str = "",
        broker_password: str = "",
        topic: Optional[str] = None,
        client_id: Optional[str] = None,
        create_publisher: bool = True,
        mqtt_client: Optional[RawMqttClient] = None,
        publisher: Optional[TemporaryAnalyticsMQTTPublisher] = None,
    ):
        """
        Set up analytics publishing on the device (optional) and subscribe to the topic.

        If create_publisher is False, provide a topic to subscribe to an existing publisher.
        You can also inject an existing RawMqttClient or TemporaryAnalyticsMQTTPublisher for testing.
        """
        topic_suffix = hashlib.sha256(analytics_data_source_key.encode()).hexdigest()[:8]
        self.topic = topic or f"ax-devil/temp/{topic_suffix}"
        self._publisher: Optional[TemporaryAnalyticsMQTTPublisher] = None
        self._client: RawMqttClient

        if publisher:
            self._publisher = publisher
        elif create_publisher:
            if device_config is None:
                raise ValueError("device_config must be provided when creating a publisher")
            self._publisher = TemporaryAnalyticsMQTTPublisher(
                device_config=device_config,
                broker_host=broker_host,
                broker_port=broker_port,
                topic=self.topic,
                client_id=client_id or self.topic,
                analytics_data_source_key=analytics_data_source_key,
                broker_username=broker_username,
                broker_password=broker_password,
            )

        self._client = mqtt_client or RawMqttClient(
            broker_host=broker_host,
            broker_port=broker_port,
            topics=[self.topic],
            message_callback=message_callback,
            worker_threads=worker_threads,
        )

    def start(self) -> None:
        """Start listening for analytics messages."""
        self._client.start()

    def stop(self) -> None:
        """Stop listening and clean up any created publisher."""
        try:
            self._client.stop()
        finally:
            if self._publisher:
                self._publisher.cleanup()
