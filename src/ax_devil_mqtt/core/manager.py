import asyncio
import threading
from typing import Any, Dict, Optional
from concurrent.futures import ThreadPoolExecutor
import logging
from dataclasses import dataclass
import time

from ax_devil_device_api import DeviceConfig
from ax_devil_device_api.features.mqtt_client import BrokerConfig

from .subscriber import MQTTSubscriber
from .replay import ReplayHandler
from .recorder import MessageRecorder
from .analytics_mqtt_stream_tmp import TemporaryAnalyticsMQTTDataStream
from .types import SimulatorConfig, MQTTStreamConfig, MQTTStreamState, MessageHandler

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
        
        # Set up the message processing chain
        self._message_processor = MessageProcessor(
            config.message_callback, 
            config.worker_threads
        )
        
        # Create recorder as an intermediary component
        self._recorder = MessageRecorder(self._message_processor.submit_message)
        
        # Store analytics stream if created
        self._analytics_stream = None
        
        # Initialize the appropriate handler based on config
        self._handler: MessageHandler = self._create_handler()
        
    def _create_handler(self) -> MessageHandler:
        """Create the appropriate handler based on configuration."""
        if self._config.device_config:
            # Device mode - use subscriber with analytics or raw topics
            if self._config.analytics_mqtt_data_source_key:
                self._analytics_stream = TemporaryAnalyticsMQTTDataStream(
                    device_config=self._config.device_config,
                    broker_config=self._config.broker_config,
                    analytics_data_source_key=self._config.analytics_mqtt_data_source_key
                )
                topics = self._analytics_stream.topics
            else:
                topics = self._config.raw_mqtt_topics
                
            return MQTTSubscriber(
                broker_host=self._config.broker_config.host,
                broker_port=self._config.broker_config.port,
                topics=topics,
                max_queue_size=self._config.max_queue_size,
                message_callback=self._recorder.record_message
            )
            
        else:
            # Simulator mode - use ReplayHandler
            if not self._config.simulator_config or not self._config.simulator_config.recording_file:
                raise ValueError("Simulator mode requires a recording file")
            handler = ReplayHandler(self._recorder.record_message)
            # Store the recording file so it can be accessed later
            handler._recording_file = self._config.simulator_config.recording_file
            return handler

    def start(self, recording_file: Optional[str] = None):
        """
        Start the stream manager.
        
        Args:
            recording_file: Optional file path to record messages to. Only valid in device mode.
        """
        if self._state.is_running:
            logger.warning("Stream manager is already running")
            return

        try:
            # Start recording if a file path is provided
            if recording_file:
                self._recorder.start_recording(recording_file)
                self._state.is_recording = True
            
            # Start the message handler
            self._handler.start()
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
            # Stop the handler
            self._handler.stop()
            
            # Stop recording if active
            if self._state.is_recording:
                self._recorder.stop_recording()
                self._state.is_recording = False
            
            # Clean up analytics stream if it exists
            if self._analytics_stream:
                try:
                    self._analytics_stream.cleanup()
                    self._analytics_stream = None
                except Exception as e:
                    logger.error(f"Error cleaning up analytics stream: {e}")
            
            # Stop the message processor
            self._message_processor.stop()
            
            self._state.is_running = False
            
            logger.info("Stream manager stopped successfully")
        except Exception as e:
            self._state.error_state = str(e)
            logger.error(f"Error during stream manager shutdown: {e}")
            raise
