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
from .device_analytics_mqtt_manager import DeviceAnalyticsMQTTManager
from .types import MQTTConfigBase, RawMQTTConfig, AnalyticsMQTTConfig, SimulationConfig, MQTTStreamState, MessageHandler

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
    def __init__(self, config: MQTTConfigBase):
        """Initialize the MQTT stream manager."""
        self._config = config
        self._config.validate()
        
        self._state = MQTTStreamState()
        
        self._message_processor = MessageProcessor(
            config.message_callback, 
            config.worker_threads
        )
        
        self._recorder = MessageRecorder(self._message_processor.submit_message)
        
        self._analytics_stream = None
        
        self._handler: MessageHandler = self._create_handler()
        
    def _create_handler(self) -> MessageHandler:
        """Create the appropriate handler based on configuration."""
        if isinstance(self._config, RawMQTTConfig):
            return MQTTSubscriber(
                broker_host=self._config.broker_config.host,
                broker_port=self._config.broker_config.port,
                topics=self._config.raw_mqtt_topics,
                max_queue_size=self._config.max_queue_size,
                message_callback=self._recorder.record_message
            )
            
        elif isinstance(self._config, AnalyticsMQTTConfig):
            self._analytics_stream = DeviceAnalyticsMQTTManager(
                device_config=self._config.device_config,
                broker_config=self._config.broker_config,
                analytics_data_source_key=self._config.analytics_mqtt_data_source_key
            )
            topics = self._analytics_stream.topics
            
            return MQTTSubscriber(
                broker_host=self._config.broker_config.host,
                broker_port=self._config.broker_config.port,
                topics=topics,
                max_queue_size=self._config.max_queue_size,
                message_callback=self._recorder.record_message
            )
            
        elif isinstance(self._config, SimulationConfig):
            handler = ReplayHandler(self._recorder.record_message)
            handler._recording_file = self._config.recording_file
            return handler
        
        else:
            raise ValueError(f"Unsupported configuration type: {type(self._config)}")

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
            if recording_file:
                self._recorder.start_recording(recording_file)
                self._state.is_recording = True
            
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
            self._handler.stop()
            
            if self._state.is_recording:
                self._recorder.stop_recording()
                self._state.is_recording = False
            
            if self._analytics_stream:
                try:
                    self._analytics_stream.cleanup()
                    self._analytics_stream = None
                except Exception as e:
                    logger.error(f"Error cleaning up analytics stream: {e}")
            
            self._message_processor.stop()
            
            self._state.is_running = False
            
            logger.info("Stream manager stopped successfully")
        except Exception as e:
            self._state.error_state = str(e)
            logger.error(f"Error during stream manager shutdown: {e}")
            raise
