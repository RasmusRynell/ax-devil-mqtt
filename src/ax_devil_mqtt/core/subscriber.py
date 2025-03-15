import paho.mqtt.client as mqtt
from typing import Callable, Dict, Any, List
import json
from datetime import datetime
import logging
import time

from .types import DataRetriever

logger = logging.getLogger(__name__)

class MQTTSubscriber(DataRetriever):
    """
    Handles MQTT subscriptions and message processing.
    This class is responsible for:
    - Managing MQTT connection for subscribing
    - Processing incoming messages
    - Maintaining subscription state
    """
    def __init__(
        self,
        broker_host: str,
        broker_port: int,
        topics: List[str],
        message_callback: Callable[[Dict[str, Any]], None],
        connection_timeout_seconds: int = 5
    ):
        self._broker_host = broker_host
        self._broker_port = broker_port
        self._topics = topics
        self._connected = False
        self._message_callback = message_callback
        self._connection_error = None
        self._connection_timeout_seconds = connection_timeout_seconds
        self._client = mqtt.Client()
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, flags, rc):
        """Internal callback when connection is established"""
        if rc == 0:
            self._connected = True
            for topic in self._topics:
                self._client.subscribe(topic)
        else:
            self._connected = False
            logger.error(f"Failed to connect to MQTT broker with code {rc}")
            self._connection_error = f"Failed to connect to MQTT broker with code {rc}"

    def _on_message(self, client, userdata, message):
        """Internal callback for handling incoming messages"""
        try:
            msg = {
                'timestamp': datetime.now().isoformat(),
                'topic': message.topic,
                'payload': message.payload.decode(),
                'qos': message.qos,
                'retain': message.retain
            }
            
            try:
                msg['payload'] = json.loads(msg['payload'])
            except json.JSONDecodeError:
                pass
            
            if self._message_callback:
                self._message_callback(msg)
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def _on_disconnect(self, client, userdata, rc):
        """Internal callback when disconnected"""
        self._connected = False
        if rc != 0:
            logger.error(f"Unexpected disconnection (code {rc})")

    def start(self):
        """
        Start the subscriber.
        """
        self._connection_error = None
        
        if not self._connected:
            logger.info(f"Connecting to MQTT broker at {self._broker_host}:{self._broker_port}")
            try:
                self._client.connect(self._broker_host, self._broker_port)
            except Exception as e:
                logger.error(f"Error connecting to MQTT broker: {e}")
                raise ConnectionError(f"Failed to connect to MQTT broker: {e}")

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

    def stop(self):
        """Stop the subscriber and clean up"""
        self._client.loop_stop()
        self._client.disconnect()
        self._connected = False
        self._message_callback = None

    def is_connected(self) -> bool:
        """Check if connected to broker"""
        return self._connected

    def add_topic(self, topic: str):
        """Subscribe to additional topic"""
        if self._connected:
            self._client.subscribe(topic)
        self._topics.append(topic)

    def remove_topic(self, topic: str):
        """Unsubscribe from a topic"""
        if self._connected:
            self._client.unsubscribe(topic)
        if topic in self._topics:
            self._topics.remove(topic) 