import json
import threading
import time
import dateutil.parser
from typing import Dict, Any, Callable, Optional
import logging

from .types import DataRetriever

logger = logging.getLogger(__name__)

class ReplayHandler(DataRetriever):
    """Handles replaying recorded messages from a JSONL file."""
    def __init__(self, message_callback: Callable[[Dict[str, Any]], None], 
                recording_file: Optional[str] = None,
                on_replay_complete: Optional[Callable[[Dict[str, float]], None]] = None):
        self._message_callback = message_callback
        self._recording_file = recording_file
        self._replay_thread = None
        self._stop_replay = threading.Event()
        self._replay_error = None
        self._on_replay_complete = on_replay_complete
            
    def is_replaying(self) -> bool:
        """Check if a replay is currently in progress."""
        return self._replay_thread is not None and self._replay_thread.is_alive()

    def start(self) -> None:
        """Start the handler, replaying messages from a recording file."""
        if self.is_replaying():
            raise RuntimeError("Replay already in progress")
        
        if self._recording_file is None:
            raise ValueError("Recording file must be provided before starting replay")
            
        self._stop_replay.clear()
        self._replay_error = None
        
        self._replay_thread = threading.Thread(
            target=self._replay_worker,
            daemon=True
        )
        self._replay_thread.start()

    def stop(self) -> None:
        """Stop the current replay if one is in progress."""
        if not self.is_replaying():
            return
            
        self._stop_replay.set()
            
        self._replay_thread.join(timeout=5)
        if self._replay_thread.is_alive():
            logger.warning("Replay thread did not terminate within timeout")
        
        self._replay_thread = None

    def _replay_worker(self) -> None:
        """Worker thread for replaying recorded messages."""
        try:
            stats = self._replay_file(self._recording_file)
            logger.info(f"Replay complete: {stats}")
            if self._on_replay_complete and not self._stop_replay.is_set():
                self._on_replay_complete()
        except FileNotFoundError:
            self._replay_error = f"Recording file not found: {self._recording_file}"
            logger.error(self._replay_error)
        except Exception as e:
            self._replay_error = f"Error during replay: {str(e)}"
            logger.error(self._replay_error)
        finally:
            self._stop_replay.clear()

    def _replay_file(self, file_path: str) -> Dict[str, float]:
        """Replay messages from a file, maintaining the original timing between messages."""
        stats = {"total_drift": 0.0, "max_drift": 0.0, "message_count": 0, "avg_drift": 0.0}
        reference_time = None
        replay_start_time = None
        
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    if self._stop_replay.is_set():
                        break
                        
                    try:
                        topic, timestamp, payload = self.get_message(line.strip())
                        
                        if reference_time is None:
                            reference_time = timestamp
                            replay_start_time = time.time()
                        
                        relative_time = timestamp - reference_time
                        target_send_time = replay_start_time + relative_time
                        
                        current_time = time.time()
                        if current_time < target_send_time and not self._stop_replay.is_set():
                            time.sleep(target_send_time - current_time)
                        
                        self._message_callback(payload)
                        
                        actual_send_time = time.time()
                        drift_ms = (actual_send_time - target_send_time) * 1000
                        stats["total_drift"] += drift_ms
                        stats["max_drift"] = max(stats["max_drift"], abs(drift_ms))
                        stats["message_count"] += 1
                        
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        
        except Exception as e:
            logger.error(f"Error during replay: {e}")
            
        if stats["message_count"] > 0:
            stats["avg_drift"] = stats["total_drift"] / stats["message_count"]
            
        return stats
    
    def get_message(self, line: str) -> Dict[str, Any]:
        """Get a message from a line of text."""
        message = json.loads(line.strip())
        timestamp = dateutil.parser.parse(message['timestamp']).timestamp()
        return message['topic'], timestamp, message['payload']