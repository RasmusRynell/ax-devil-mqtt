import paho.mqtt.client as mqtt
from typing import Dict, Any, Union
import json
import threading
import time
from datetime import datetime
from pathlib import Path
import dateutil.parser

class MQTTPublisher:
    """
    Handles MQTT message publishing.
    This class is responsible for:
    - Managing MQTT connection for publishing
    - Message formatting and delivery
    - Maintaining connection state
    - Replaying recorded MQTT messages from JSONL files
    """
    def __init__(self, broker_host: str, broker_port: int):
        self._broker_host = broker_host
        self._broker_port = broker_port
        self._connected = False
        self._client = mqtt.Client()
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._lock = threading.Lock()  # For thread-safe publishing
        self._replay_thread = None
        self._stop_replay = threading.Event()

    def _on_connect(self, client, userdata, flags, rc):
        """Internal callback when connection is established"""
        if rc == 0:
            self._connected = True
        else:
            self._connected = False
            raise ConnectionError(f"Failed to connect to MQTT broker with code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """Internal callback when disconnected"""
        self._connected = False
        if rc != 0:
            print(f"Unexpected disconnection (code {rc})")

    def start(self):
        """Start the publisher"""
        if not self._connected:
            self._client.connect(self._broker_host, self._broker_port)
            self._client.loop_start()

    def stop(self):
        """Stop the publisher and clean up"""
        with self._lock:
            if self._connected:
                self._client.loop_stop()
                self._client.disconnect()
                self._connected = False

    def publish(self, topic: str, payload: Union[Dict, str], qos: int = 1) -> bool:
        """
        Publish a message to a topic.
        
        Args:
            topic: The topic to publish to
            payload: The message payload (dict or string)
            qos: Quality of Service (0, 1, or 2)
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        if not self._connected:
            return False

        try:
            with self._lock:
                # Convert dict to JSON string if needed
                if isinstance(payload, dict):
                    payload = json.dumps(payload)
                
                # Publish and wait for confirmation
                result = self._client.publish(topic, payload, qos=qos)
                result.wait_for_publish()
                return result.is_published()
        except Exception as e:
            print(f"Error publishing message: {e}")
            return False

    def is_connected(self) -> bool:
        """Check if connected to broker"""
        return self._connected 

    def replay_recording(self, recording_file: str) -> None:
        """
        Replay messages from a JSONL recording file with original timing.
        
        Args:
            recording_file: Path to the JSONL recording file
        """
        if not self._connected:
            raise ConnectionError("Publisher not connected to broker")
            
        if self._replay_thread and self._replay_thread.is_alive():
            raise RuntimeError("Replay already in progress")
            
        self._stop_replay.clear()
        self._replay_thread = threading.Thread(
            target=self._replay_worker,
            args=(recording_file,),
            daemon=True
        )
        self._replay_thread.start()

    def stop_replay(self) -> None:
        """Stop the current replay if one is in progress."""
        if self._replay_thread and self._replay_thread.is_alive():
            self._stop_replay.set()
            self._replay_thread.join()
            self._replay_thread = None

    def _replay_worker(self, recording_file: str) -> None:
        """Worker thread for replaying recorded messages."""
        total_drift = 0
        max_drift = 0
        message_count = 0
        
        try:
            with open(recording_file, 'r') as f:
                messages = [json.loads(line.strip()) for line in f] # Could be bottleneck if file is large
                if not messages:
                    return

                # Parse timestamps once at the start
                message_times = [
                    dateutil.parser.parse(msg['timestamp']).timestamp() 
                    for msg in messages
                ]
                
                # Get start time and first message time
                replay_start_time = time.time()
                first_msg_time = message_times[0]

                for i, (message, msg_timestamp) in enumerate(zip(messages, message_times)):
                    if self._stop_replay.is_set():
                        break

                    try:
                        # Calculate when this message should be sent
                        relative_msg_time = msg_timestamp - first_msg_time
                        target_send_time = replay_start_time + relative_msg_time

                        # Wait until it's time to send this message
                        current_time = time.time()
                        if current_time < target_send_time:
                            time.sleep(target_send_time - current_time)

                        # Extract and validate message fields
                        topic = message.get('topic')
                        payload = message.get('payload')
                        qos = message.get('qos', 1)

                        if not topic or payload is None:
                            print(f"Skipping message missing required fields: {message}")
                            continue

                        # Publish the message
                        if self.publish(topic, payload, qos):
                            # Only calculate drift for successfully published messages
                            actual_send_time = time.time()
                            drift_ms = (actual_send_time - target_send_time) * 1000
                            total_drift += drift_ms
                            max_drift = max(max_drift, abs(drift_ms))
                            message_count += 1
                            
                            print(f"Message {i+1}/{len(messages)} - Drift: {drift_ms:.2f}ms " + 
                                  f"(Target: {datetime.fromtimestamp(target_send_time).isoformat()}, " +
                                  f"Actual: {datetime.fromtimestamp(actual_send_time).isoformat()})")
                        else:
                            print(f"Failed to publish message {i+1}")

                    except Exception as e:
                        print(f"Error processing message {i+1}: {e}")

                # Print drift statistics
                if message_count > 0:
                    avg_drift = total_drift / message_count
                    print(f"\nReplay Statistics:")
                    print(f"Total messages: {message_count}")
                    print(f"Average drift: {avg_drift:.2f}ms")
                    print(f"Maximum drift: {max_drift:.2f}ms")

        except FileNotFoundError:
            print(f"Recording file not found: {recording_file}")
        except Exception as e:
            print(f"Error reading recording file: {e}")
        finally:
            self._stop_replay.clear() 