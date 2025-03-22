import asyncio
import hashlib
import threading
from typing import Any, Dict, Optional, List, Callable
from concurrent.futures import ThreadPoolExecutor
import logging

from .subscriber import MQTTSubscriber
from .replay import ReplayHandler
from .recorder import Recorder
from .temporary_analytics_mqtt_publisher import TemporaryAnalyticsMQTTPublisher
from .types import DataRetriever
from ax_devil_device_api import DeviceConfig

logger = logging.getLogger(__name__)

class MessageProcessor:
    """Handles message processing and callback execution."""
    
    def __init__(self, callback, worker_threads: int):
        self.callback = callback
        self._executor = ThreadPoolExecutor(max_workers=worker_threads)
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def process_message(self, message: Dict[str, Any]):
        """Process a message using the provided callback."""
        if not self.callback:
            return

        try:
            if asyncio.iscoroutinefunction(self.callback):
                asyncio.run(self.callback(message))
            else:
                self.callback(message)
        except Exception as e:
            logger.error(
                f"Error in message callback: {str(e)}. "
                f"Message topic: {message.get('topic', 'unknown')}, "
                f"Message size: {len(str(message))} bytes"
            )
            raise  # Re-raise to let the executor handle the failure

    def submit_message(self, message: Dict[str, Any]) -> None:
        """Submit a message for processing."""
        with self._lock:
            if self._stop_event.is_set():
                return
                
            try:
                self._executor.submit(self.process_message, message)
            except RuntimeError:
                logger.warning("Executor is shutting down, message dropped")

    def stop(self):
        """Stop message processing."""
        if self._stop_event.is_set():
            return
            
        self._stop_event.set()
        try:
            self._executor.shutdown(wait=True)
        except Exception as e:
            logger.error(f"Error during executor shutdown: {e}")
        logger.info("Message processor stopped")

class StreamManagerBase:
    """Base class for all stream managers."""
    def __init__(self, message_callback: Callable[[Dict[str, Any]], None], worker_threads: int = 2):
        self._is_running = False
        self._is_recording = False
        self._message_processor = MessageProcessor(message_callback, worker_threads)
        self._recorder = Recorder()
        self._data_retriever: Optional[DataRetriever] = None

    def start(self, recording_file: Optional[str] = None):
        """Start the stream manager with optional recording."""
        if self._is_running:
            logger.warning("Stream manager is already running")
            return

        try:
            if recording_file:
                self._recorder.start_recording(recording_file)
                self._is_recording = True
                
            if self._data_retriever:
                self._data_retriever.start()
                self._is_running = True
                logger.info("Stream manager started successfully")
            else:
                raise RuntimeError("Handler not initialized")
        except Exception as e:
            logger.error(f"Failed to start stream manager: {e}")
            self.stop()
            raise

    def stop(self):
        """Stop the stream manager and clean up resources."""
        if not self._is_running:
            return

        try:
            if self._data_retriever:
                self._data_retriever.stop()
            
            if self._is_recording:
                self._recorder.stop_recording()
                self._is_recording = False
                
            self._message_processor.stop()
            self._is_running = False
            
            logger.info("Stream manager stopped successfully")
        except Exception as e:
            logger.error(f"Error during stream manager shutdown: {e}")
            raise

    def _on_message_callback(self, message: Dict[str, Any]):
        """Callback for when a message is received."""
        if self._is_recording:
            self._recorder.record_message(message)
        self._message_processor.submit_message(message)
class RawMQTTManager(StreamManagerBase):
    """Manager for handling raw MQTT message streams."""
    def __init__(
        self, 
        broker_host: str,
        broker_port: int,
        topics: List[str],
        message_callback: Callable[[Dict[str, Any]], None],
        worker_threads: int = 2
    ):
        if not topics:
            raise ValueError("MQTT topics must be provided")
            
        super().__init__(message_callback, worker_threads)
        self._broker_host = broker_host
        self._broker_port = broker_port
        self._topics = topics
        self._data_retriever = MQTTSubscriber(
            broker_host=self._broker_host,
            broker_port=self._broker_port,
            topics=self._topics,
            message_callback=self._on_message_callback
        )

class AnalyticsManager(StreamManagerBase):
    """Manager for handling analytics MQTT message streams."""
    def __init__(
        self,
        broker_host: str,
        broker_port: int,
        device_config: DeviceConfig,
        analytics_data_source_key: str,
        message_callback: Callable[[Dict[str, Any]], None],
        worker_threads: int = 2,
        broker_username: str = "",
        broker_password: str = ""
    ):
        if not analytics_data_source_key:
            raise ValueError("analytics_data_source_key must be provided")
            
        super().__init__(message_callback, worker_threads)
        
        small_hash = hashlib.sha256(analytics_data_source_key.encode()).hexdigest()[:8]
        self._analytics_stream = TemporaryAnalyticsMQTTPublisher(
            device_config=device_config,
            broker_host=broker_host,
            broker_port=broker_port,
            topic=f"ax-devil/temp/{small_hash}",
            client_id=f"ax-devil/temp/{small_hash}",
            analytics_data_source_key=analytics_data_source_key,
            broker_username=broker_username,
            broker_password=broker_password
        )
        
        self._data_retriever = MQTTSubscriber(
            broker_host=broker_host,
            broker_port=broker_port,
            topics=[f"ax-devil/temp/{small_hash}"],
            message_callback=self._on_message_callback
        )
        
    def stop(self):
        """Stop the analytics manager and clean up resources."""
        try:
            super().stop()
            
            if self._analytics_stream:
                try:
                    self._analytics_stream.cleanup()
                    self._analytics_stream = None
                except Exception as e:
                    logger.error(f"Error cleaning up analytics stream: {e}")
        except Exception as e:
            logger.error(f"Error during analytics manager shutdown: {e}")
            raise

class ReplayManager(StreamManagerBase):
    """Manager for replaying MQTT message streams from recorded files."""
    def __init__(
        self,
        recording_file: str,
        message_callback: Callable[[Dict[str, Any]], None],
        on_replay_complete: Callable[[], None] = None,
        worker_threads: int = 2
    ):
        if not recording_file:
            raise ValueError("recording_file must be provided")
            
        super().__init__(message_callback, worker_threads)
        self._data_retriever = ReplayHandler(self._on_message_callback, recording_file, on_replay_complete)