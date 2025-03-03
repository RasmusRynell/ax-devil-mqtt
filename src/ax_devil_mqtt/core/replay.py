import json
import threading
import time
from datetime import datetime
import dateutil.parser
from typing import Dict, Any, Callable, Optional

class ReplayHandler:
    """
    Handles replaying recorded messages from a JSONL file.
    This class is responsible for:
    - Reading messages from a JSONL recording file
    - Maintaining original message timing
    - Directly calling message callbacks without MQTT
    """
    def __init__(self, message_callback: Callable[[Dict[str, Any]], None]):
        self._message_callback = message_callback
        self._replay_thread = None
        self._stop_replay = threading.Event()
        self._lock = threading.Lock()

    def start_replay(self, recording_file: str) -> None:
        """
        Start replaying messages from a JSONL recording file with original timing.
        
        Args:
            recording_file: Path to the JSONL recording file
        """
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
                messages = [json.loads(line.strip()) for line in f]
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

                        # Call the message callback directly
                        self._message_callback(message)
                        
                        # Calculate drift for monitoring
                        actual_send_time = time.time()
                        drift_ms = (actual_send_time - target_send_time) * 1000
                        total_drift += drift_ms
                        max_drift = max(max_drift, abs(drift_ms))
                        message_count += 1
                        
                        print(f"Message {i+1}/{len(messages)} - Drift: {drift_ms:.2f}ms " + 
                              f"(Target: {datetime.fromtimestamp(target_send_time).isoformat()}, " +
                              f"Actual: {datetime.fromtimestamp(actual_send_time).isoformat()})")

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