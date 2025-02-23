import asyncio
import threading
from typing import Any, Dict, Optional
from concurrent.futures import ThreadPoolExecutor
import logging
from dataclasses import dataclass

from ax_devil_device_api import DeviceConfig
from ax_devil_device_api.features.mqtt_client import BrokerConfig

from .subscriber import MQTTSubscriber
from .publisher import MQTTPublisher
from .analytics import TemporaryAnalyticsMQTTDataStream
from .types import SimulatorConfig, MQTTStreamConfig, MQTTStreamState

logger = logging.getLogger(__name__)

class MessageProcessor:
    """Handles message processing and callback execution."""
    
    def __init__(self, callback, worker_threads: int):
        self.callback = callback
        self._executor = ThreadPoolExecutor(max_workers=worker_threads)
        self._stop_event = threading.Event()
        self._worker_threads = []
        self._shutdown_lock = threading.Lock()  # Add lock for shutdown coordination

    def process_message(self, message: Dict[str, Any]):
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
            logger.error(f"Error in message callback: {e}")

    def worker_loop(self, message_queue):
        """Worker thread for processing messages."""
        while not self._stop_event.is_set():
            message = message_queue.get_message(timeout=1.0)
            if message:
                # Check if we can still submit tasks
                with self._shutdown_lock:
                    if not self._stop_event.is_set():
                        try:
                            self._executor.submit(self.process_message, message)
                        except RuntimeError:
                            # Executor is shut down, exit the loop
                            break

    def start(self, message_queue):
        """Start message processing workers."""
        for _ in range(self._executor._max_workers):
            worker = threading.Thread(target=self.worker_loop, args=(message_queue,), daemon=True)
            worker.start()
            self._worker_threads.append(worker)

    def stop(self):
        """Stop message processing."""
        with self._shutdown_lock:
            self._stop_event.set()
        
        # Wait for workers to finish their current tasks
        for worker in self._worker_threads:
            worker.join(timeout=2)
            
        # Now safe to shutdown the executor
        self._executor.shutdown(wait=True)

class MQTTStreamManager:
    """
    Core manager class for handling MQTT message streams.
    Supports both real-time data streams and simulated replay.
    """
    def __init__(self, config: MQTTStreamConfig):
        """Initialize the MQTT stream manager."""
        self._config = config
        self._config.validate()
        
        self._state = MQTTStreamState()
        self._publisher = None
        self._analytics_stream = None
        self._subscriber = None
        
        self._message_processor = MessageProcessor(
            config.message_callback, 
            config.worker_threads
        )
        
        self._setup_stream()

    def _setup_stream(self):
        """Setup the appropriate stream based on configuration."""
        if self._config.device_config:
            self._setup_device_mode()
        else:
            self._setup_simulator_mode()

        # Setup subscriber
        self._subscriber = MQTTSubscriber(
            broker_host=self._config.broker_config.host,
            broker_port=self._config.broker_config.port,
            topics=self._state.current_topics,
            max_queue_size=self._config.max_queue_size
        )

    def _setup_device_mode(self):
        """Setup stream for device mode."""
        if self._config.analytics_mqtt_data_source_key:
            self._analytics_stream = TemporaryAnalyticsMQTTDataStream(
                device_config=self._config.device_config,
                broker_config=self._config.broker_config,
                analytics_data_source_key=self._config.analytics_mqtt_data_source_key
            )
            self._state.current_topics = self._analytics_stream.topics
        else:
            self._state.current_topics = self._config.raw_mqtt_topics

    def _setup_simulator_mode(self):
        """Setup stream for simulator mode."""
        self._publisher = MQTTPublisher(
            broker_host=self._config.broker_config.host,
            broker_port=self._config.broker_config.port
        )
        # In simulator mode, subscribe to all topics
        self._state.current_topics = ["#"]

    def start(self):
        """Start the stream manager."""
        if self._state.is_running:
            logger.warning("Stream manager is already running")
            return

        try:
            self._subscriber.start()
            
            if self._publisher:
                self._publisher.start()
            
            self._message_processor.start(self._subscriber)
            self._state.is_running = True
            logger.info("Stream manager started successfully")
        except Exception as e:
            self._state.error_state = str(e)
            logger.error(f"Failed to start stream manager: {e}")
            self.stop()
            raise

    def stop(self):
        """Stop the stream manager and clean up resources."""
        if not self._state.is_running:
            return

        try:
            self._message_processor.stop()
            self._subscriber.stop()
            
            if self._publisher:
                self._publisher.stop_replay()
                self._publisher.stop()
            
            self._state.is_running = False
            logger.info("Stream manager stopped successfully")
        except Exception as e:
            self._state.error_state = str(e)
            logger.error(f"Error during stream manager shutdown: {e}")
            raise

    def start_recording(self, filepath: str):
        """Enable message recording to specified file."""
        if self._state.is_recording:
            logger.warning("Recording is already in progress")
            return

        try:
            self._subscriber.start_recording(filepath)
            self._state.is_recording = True
            logger.info(f"Started recording to {filepath}")
        except Exception as e:
            self._state.error_state = str(e)
            logger.error(f"Failed to start recording: {e}")
            raise

    def stop_recording(self):
        """Disable message recording."""
        if not self._state.is_recording:
            return

        try:
            self._subscriber.stop_recording()
            self._state.is_recording = False
            logger.info("Recording stopped")
        except Exception as e:
            self._state.error_state = str(e)
            logger.error(f"Failed to stop recording: {e}")
            raise

    def start_replay(self, recording_file: str) -> None:
        """Start replaying messages from a recording file."""
        if not self._publisher:
            raise RuntimeError("Publisher not available - manager was not initialized with simulator config")
        
        if self._state.is_replaying:
            logger.warning("Replay is already in progress")
            return

        try:
            self._publisher.replay_recording(recording_file)
            self._state.is_replaying = True
            logger.info(f"Started replay from {recording_file}")
        except Exception as e:
            self._state.error_state = str(e)
            logger.error(f"Failed to start replay: {e}")
            raise

    def stop_replay(self) -> None:
        """Stop the current replay if one is in progress."""
        if not self._state.is_replaying:
            return

        try:
            self._publisher.stop_replay()
            self._state.is_replaying = False
            logger.info("Replay stopped")
        except Exception as e:
            self._state.error_state = str(e)
            logger.error(f"Failed to stop replay: {e}")
            raise
