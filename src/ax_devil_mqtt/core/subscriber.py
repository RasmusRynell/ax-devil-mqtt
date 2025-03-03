import paho.mqtt.client as mqtt
from typing import Callable, Dict, Any, Optional, List
import threading
import queue
import json
import os
from datetime import datetime

class MQTTSubscriber:
    """
    Handles MQTT subscriptions and message processing.
    This class is responsible for:
    - Managing MQTT connection for subscribing
    - Processing incoming messages
    - Maintaining subscription state
    - Recording messages to file for debugging/testing
    """
    def __init__(
        self,
        broker_host: str,
        broker_port: int,
        topics: List[str],
        max_queue_size: int = 1000
    ):
        self._broker_host = broker_host
        self._broker_port = broker_port
        self._topics = topics
        self._connected = False
        self._stop_event = threading.Event()
        self._message_callback = None
        
        # Recording functionality
        self._recording_enabled = False
        self._recording_file = None
        
        # Set up MQTT client
        self._client = mqtt.Client()
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, flags, rc):
        """Internal callback when connection is established"""
        if rc == 0:
            self._connected = True
            # Subscribe to all configured topics
            for topic in self._topics:
                print(f"Subscribing to topic: {topic}")
                self._client.subscribe(topic)
        else:
            self._connected = False
            raise ConnectionError(f"Failed to connect to MQTT broker with code {rc}")

    def _on_message(self, client, userdata, message):
        """Internal callback for handling incoming messages"""
        try:
            # Parse message into a structured format with timestamp
            msg = {
                'timestamp': datetime.now().isoformat(),
                'topic': message.topic,
                'payload': message.payload.decode(),
                'qos': message.qos,
                'retain': message.retain
            }
            
            # Try to parse JSON payload if possible
            try:
                msg['payload'] = json.loads(msg['payload'])
            except json.JSONDecodeError:
                pass  # Keep payload as string if not JSON
            
            # Record message if enabled
            if self._recording_enabled and self._recording_file:
                # Write message to file immediately
                json.dump(msg, self._recording_file)
                self._recording_file.write('\n')
                self._recording_file.flush()
                
            # Forward to callback if set
            if self._message_callback:
                self._message_callback(msg)
        except Exception as e:
            print(f"Error processing message: {e}")

    def _on_disconnect(self, client, userdata, rc):
        """Internal callback when disconnected"""
        self._connected = False
        if rc != 0:
            print(f"Unexpected disconnection (code {rc})")

    def start(self, message_callback: Optional[Callable[[Dict[str, Any]], None]] = None):
        """
        Start the subscriber with an optional message callback.
        
        Args:
            message_callback: Optional callback function to handle messages
        """
        self._message_callback = message_callback
        
        if not self._connected:
            print(f"Connecting to MQTT broker at {self._broker_host}:{self._broker_port}")
            self._client.connect(self._broker_host, self._broker_port)

        # Start MQTT loop in a separate thread
        self._client.loop_start()

    def stop(self):
        """Stop the subscriber and clean up"""
        self._stop_event.set()
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

    def start_recording(self, filepath: str):
        """Start recording messages to file."""
        if self._recording_enabled:
            self.stop_recording()
            
        try:
            # Open file in append mode
            self._recording_file = open(filepath, 'a')
            self._recording_enabled = True
        except IOError as e:
            raise IOError(f"Failed to open recording file: {e}")

    def stop_recording(self):
        """Stop recording and close file."""
        self._recording_enabled = False
        if self._recording_file:
            self._recording_file.close()
            self._recording_file = None

    def __del__(self):
        """Clean up resources."""
        self.stop_recording() 