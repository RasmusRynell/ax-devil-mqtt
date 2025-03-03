"""
Shared types and configurations for the AX Devil MQTT package.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Callable, Union, Coroutine, Protocol, runtime_checkable
from abc import ABC, abstractmethod
from ax_devil_device_api import DeviceConfig
from ax_devil_device_api.features.mqtt_client import BrokerConfig

# Define the common interface for message handlers
class MessageHandler(ABC):
    """
    Abstract base class defining the interface for all message handlers.
    Both MQTTSubscriber and ReplayHandler should implement this interface.
    """
    @abstractmethod
    def start(self) -> None:
        """
        Start the message handler.
        """
        pass
        
    @abstractmethod
    def stop(self) -> None:
        """Stop the message handler and clean up resources."""
        pass

@dataclass
class SimulatorConfig:
    """Configuration for MQTT message simulation."""
    recording_file: Optional[str] = None  # Path to recording file for replay

@dataclass
class MQTTStreamConfig:
    """Configuration for MQTT stream manager."""
    broker_config: BrokerConfig
    raw_mqtt_topics: Optional[List[str]] = None
    analytics_mqtt_data_source_key: Optional[str] = None
    message_callback: Optional[Callable[[Dict[str, Any]], Union[None, Coroutine[Any, Any, None]]]] = None
    device_config: Optional[DeviceConfig] = None
    simulator_config: Optional[SimulatorConfig] = None
    max_queue_size: int = 1000
    worker_threads: int = 4

    def validate(self) -> None:
        """Validate the configuration."""
        # Validate mode configuration
        if self.device_config and self.simulator_config:
            raise ValueError("Cannot use both device and simulator configurations simultaneously")
        if not (self.device_config or self.simulator_config):
            raise ValueError("Either device_config or simulator_config must be provided")
            
        # Validate MQTT topic configuration for device mode
        if self.device_config:
            if self.raw_mqtt_topics and self.analytics_mqtt_data_source_key:
                raise ValueError("Cannot use both raw and analytics MQTT topics simultaneously")
            if not (self.raw_mqtt_topics or self.analytics_mqtt_data_source_key):
                raise ValueError("In device mode, either raw_mqtt_topics or analytics_mqtt_data_source_key must be provided")
        else:  # simulator mode
            if self.analytics_mqtt_data_source_key:
                raise ValueError("analytics_mqtt_data_source_key is not valid in simulator mode")

@dataclass
class MQTTStreamState:
    """Internal state management for MQTT stream."""
    is_running: bool = False
    is_recording: bool = False
    is_replaying: bool = False
    current_topics: List[str] = None
    error_state: Optional[str] = None 