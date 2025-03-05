import json
import threading
import time
from datetime import datetime
import dateutil.parser
from typing import Dict, Any, Callable, Optional
import logging

from .types import MessageHandler

logger = logging.getLogger(__name__)

class ReplayHandler(MessageHandler):
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
        self._recording_file = None
        self._replay_error = None
        self._completion_callback = None

    def set_completion_callback(self, callback: Callable[[], None]) -> None:
        """Set a callback to be called when replay is complete."""
        self._completion_callback = callback

    def start(self) -> None:
        """
        Start the handler, replaying messages from a recording file.
        """
        if self._replay_thread and self._replay_thread.is_alive():
            raise RuntimeError("Replay already in progress")
        
        if self._recording_file is None:
            raise ValueError("Recording file must be provided during initialization")
            
        self._stop_replay.clear()
        self._replay_thread = threading.Thread(
            target=self._replay_worker,
            args=(self._recording_file,),
            daemon=True
        )
        self._replay_thread.start()

    def stop(self) -> None:
        """Stop the current replay if one is in progress."""
        if self._replay_thread and self._replay_thread.is_alive():
            self._stop_replay.set()
            self._replay_thread.join(timeout=5)
            if self._replay_thread.is_alive():
                logger.warning("Replay thread did not terminate within timeout")
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
                    logger.warning(f"No messages found in recording file: {recording_file}")
                    return

                message_times = [
                    dateutil.parser.parse(msg['timestamp']).timestamp() 
                    for msg in messages
                ]
                
                replay_start_time = time.time()
                first_msg_time = message_times[0]

                for i, (message, msg_timestamp) in enumerate(zip(messages, message_times)):
                    if self._stop_replay.is_set():
                        break

                    try:
                        relative_msg_time = msg_timestamp - first_msg_time
                        target_send_time = replay_start_time + relative_msg_time

                        current_time = time.time()
                        if current_time < target_send_time:
                            time.sleep(target_send_time - current_time)

                        topic = message.get('topic')
                        payload = message.get('payload')
                        qos = message.get('qos', 1)

                        if not topic or payload is None:
                            logger.warning(f"Skipping message missing required fields: {message}")
                            continue

                        self._message_callback(message)
                        
                        # Calculate drift for monitoring
                        actual_send_time = time.time()
                        drift_ms = (actual_send_time - target_send_time) * 1000
                        total_drift += drift_ms
                        max_drift = max(max_drift, abs(drift_ms))
                        message_count += 1
                        
                        logger.info(f"Message {i+1}/{len(messages)} - Drift: {drift_ms:.2f}ms " + 
                              f"(Target: {datetime.fromtimestamp(target_send_time).isoformat()}, " +
                              f"Actual: {datetime.fromtimestamp(actual_send_time).isoformat()})")

                    except Exception as e:
                        logger.error(f"Error processing message {i+1}: {e}")

                # Print drift statistics
                if message_count > 0:
                    avg_drift = total_drift / message_count
                    logger.info(f"\nReplay Statistics:")
                    logger.info(f"Total messages: {message_count}")
                    logger.info(f"Average drift: {avg_drift:.2f}ms")
                    logger.info(f"Maximum drift: {max_drift:.2f}ms")

        except FileNotFoundError:
            logger.error(f"Recording file not found: {recording_file}")
            self._replay_error = f"Recording file not found: {recording_file}"
        except Exception as e:
            logger.error(f"Error reading recording file: {e}")
            self._replay_error = f"Error reading recording file: {e}"
        finally:
            self._stop_replay.clear()
            if self._completion_callback:
                self._completion_callback() 