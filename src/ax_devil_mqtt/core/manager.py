import asyncio
import threading
from typing import Any, Dict, Optional, Callable, Union, Coroutine, List
from concurrent.futures import ThreadPoolExecutor
import time
from dataclasses import dataclass

from ax_devil import CameraConfig
from ax_devil.features.mqtt_client import BrokerConfig

from .subscriber import MQTTSubscriber
from .publisher import MQTTPublisher
from .analytics import TemporaryAnalyticsMQTTDataStream
from .types import SimulatorConfig

class MQTTStreamManager:
    """
    Core manager class for handling MQTT message streams.
    Supports both real-time data streams and simulated replay.
    
    Responsible for:
    - Message handling and state management
    - Message processing and callbacks
    - Stream coordination
    - Message publishing and simulation (when simulator config is provided)

    The manager can operate in two modes:
    1. Camera Mode: When provided with camera_config, connects to an Axis camera
        Sub-modes:
        A. Subscribes to raw MQTT topics, the manager will NOT automatically configure the camera
        B. Subscribes to analytics MQTT topics, the manager will automatically configure the camera 
            and read from the analytics data source key. When the manager is destroyed, it will 
            automatically revert the camera to its previous configuration.
    2. Simulator Mode: When provided with simulator_config, replays recorded data
    """
    def __init__(
        self,
        broker_config: BrokerConfig,
        raw_mqtt_topics: Optional[List[str]] = None,
        analytics_mqtt_data_source_key: Optional[str] = None,
        message_callback: Optional[Callable[[Dict[str, Any]], Union[None, Coroutine[Any, Any, None]]]] = None,
        camera_config: Optional[CameraConfig] = None,
        simulator_config: Optional[SimulatorConfig] = None,
        max_queue_size: int = 1000,
        worker_threads: int = 4
    ):
        """
        Initialize the MQTT stream manager. 

        Args:
            broker_config: MQTT broker configuration (host, port, etc.)
            raw_mqtt_topics: List of raw MQTT topics to subscribe to. Mutually exclusive with analytics_mqtt_data_source_key.
            analytics_mqtt_data_source_key: Key for analytics data source. Mutually exclusive with raw_mqtt_topics.
            message_callback: Optional callback for processing received messages.
                            Can be synchronous or asynchronous.
            camera_config: Configuration for connecting to an Axis camera.
                         Mutually exclusive with simulator_config.
            simulator_config: Configuration for replay mode.
                            Mutually exclusive with camera_config.
            max_queue_size: Maximum number of messages to queue (default: 1000)
            worker_threads: Number of worker threads for message processing (default: 4)
            
        Raises:
            ValueError: If neither or both camera_config and simulator_config are provided
            ValueError: If neither or both raw_mqtt_topics and analytics_mqtt_data_source_key are provided
        """
        self._publisher = None
        self._analytics_stream = None
        self._subscriber = None
        self.callback = message_callback
        self._stop_event = threading.Event()
        
        # Validate configuration modes
        if camera_config and simulator_config:
            raise ValueError("Cannot use both camera and simulator configurations simultaneously")
        if not (camera_config or simulator_config):
            raise ValueError("Either camera_config or simulator_config must be provided")
            
        # Validate MQTT topic configuration for camera mode
        if camera_config:
            if raw_mqtt_topics and analytics_mqtt_data_source_key:
                raise ValueError("Cannot use both raw and analytics MQTT topics simultaneously")
            if not (raw_mqtt_topics or analytics_mqtt_data_source_key):
                raise ValueError("In camera mode, either raw_mqtt_topics or analytics_mqtt_data_source_key must be provided")
        else:  # simulator mode
            if analytics_mqtt_data_source_key:
                raise ValueError("analytics_mqtt_data_source_key is not valid in simulator mode")
            # Note: raw_mqtt_topics is ignored in simulator mode as topics come from recording

        # Setup stream based on configuration
        if camera_config:
            if analytics_mqtt_data_source_key:
                self._analytics_stream = TemporaryAnalyticsMQTTDataStream(
                    camera_config=camera_config,
                    broker_config=broker_config,
                    analytics_data_source_key=analytics_mqtt_data_source_key
                )
                self.topics = self._analytics_stream.topics
            else:
                self.topics = raw_mqtt_topics
        else: # simulator_config
            self._publisher = MQTTPublisher(
                broker_host=broker_config.host,
                broker_port=broker_config.port
            )
            # In simulator mode, topics will be determined from the recording
            # Ignore raw_mqtt_topics as they're not relevant for replay
            self.topics = ["#"]  # Subscribe to all topics during replay

        # Setup subscriber based on MQTT mode
        self._subscriber = MQTTSubscriber(
            broker_host=broker_config.host,
            broker_port=broker_config.port,
            topics=self.topics,
            max_queue_size=max_queue_size
        )
        
        # Initialize thread pool for message processing
        self._executor = ThreadPoolExecutor(max_workers=worker_threads)
        self._worker_threads = []

    def _process_message(self, message: Dict[str, Any]):
        """Process a message using the provided callback."""
        if not self.callback:
            return

        try:
            if asyncio.iscoroutinefunction(self.callback):
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                loop.run_until_complete(self.callback(message))
            else:
                self.callback(message)
        except Exception as e:
            print(f"Error in message callback: {e}")

    def _worker_loop(self):
        """Worker thread for processing messages."""
        while not self._stop_event.is_set():
            message = self._subscriber.get_message(timeout=1.0)
            if message:
                self._executor.submit(self._process_message, message)

    def start(self):
        """Start the stream manager."""
        self._subscriber.start()
        
        if self._publisher:
            self._publisher.start()
        
        for _ in range(self._executor._max_workers):
            worker = threading.Thread(target=self._worker_loop, daemon=True)
            worker.start()
            self._worker_threads.append(worker)

    def stop(self):
        """Stop the stream manager and clean up resources."""
        self._stop_event.set()
        self._subscriber.stop()
        
        if self._publisher:
            self._publisher.stop_replay()
            self._publisher.stop()
            
        self._executor.shutdown(wait=True)
        
        for worker in self._worker_threads:
            worker.join(timeout=2)

    def start_recording(self, filepath: str):
        """Enable message recording to specified file."""
        self._subscriber.start_recording(filepath)

    def stop_recording(self):
        """Disable message recording."""
        self._subscriber.stop_recording()

    def start_replay(self, recording_file: str) -> None:
        """
        Start replaying messages from a recording file.
        
        Args:
            recording_file: Path to the recording file
            
        Raises:
            RuntimeError: If publisher is not initialized
        """
        if not self._publisher:
            raise RuntimeError("Publisher not available - DeviceMQTTManager was not initialized with simulator config")
            
        self._publisher.replay_recording(recording_file)

    def stop_replay(self) -> None:
        """Stop the current replay if one is in progress."""
        if self._publisher:
            self._publisher.stop_replay()
