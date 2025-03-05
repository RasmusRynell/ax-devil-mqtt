"""
Shared types and configurations for the AX Devil MQTT package.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable, Union, Coroutine, Protocol, runtime_checkable
from abc import ABC, abstractmethod
from ax_devil_device_api import DeviceConfig
from ax_devil_device_api.features.mqtt_client import BrokerConfig


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

class MQTTConfigBase(ABC):
    """Base interface for all MQTT configurations."""
    @abstractmethod
    def validate(self) -> None:
        """Validate the configuration."""
        pass

class RawMQTTConfig(MQTTConfigBase):
    """Configuration for raw MQTT topics subscription."""
    def __init__(
        self,
        broker_config: BrokerConfig,
        device_config: DeviceConfig,
        raw_mqtt_topics: List[str],
        message_callback: Optional[Callable[[Dict[str, Any]], Union[None, Coroutine[Any, Any, None]]]] = None,
        max_queue_size: int = 1000,
        worker_threads: int = 4
    ):
        self.broker_config = broker_config
        self.device_config = device_config
        self.raw_mqtt_topics = raw_mqtt_topics
        self.message_callback = message_callback
        self.max_queue_size = max_queue_size
        self.worker_threads = worker_threads
    
    def validate(self) -> None:
        """Validate the raw MQTT configuration."""
        if not self.raw_mqtt_topics:
            raise ValueError("raw_mqtt_topics must be provided")

class AnalyticsMQTTConfig(MQTTConfigBase):
    """Configuration for analytics MQTT subscription."""
    def __init__(
        self,
        broker_config: BrokerConfig,
        device_config: DeviceConfig,
        analytics_mqtt_data_source_key: str,
        message_callback: Optional[Callable[[Dict[str, Any]], Union[None, Coroutine[Any, Any, None]]]] = None,
        max_queue_size: int = 1000,
        worker_threads: int = 4
    ):
        self.broker_config = broker_config
        self.device_config = device_config
        self.analytics_mqtt_data_source_key = analytics_mqtt_data_source_key
        self.message_callback = message_callback
        self.max_queue_size = max_queue_size
        self.worker_threads = worker_threads
    
    def validate(self) -> None:
        """Validate the analytics MQTT configuration."""
        if not self.analytics_mqtt_data_source_key:
            raise ValueError("analytics_mqtt_data_source_key must be provided")

class SimulationConfig(MQTTConfigBase):
    """Configuration for MQTT message simulation/replay."""
    def __init__(
        self,
        recording_file: str,
        message_callback: Optional[Callable[[Dict[str, Any]], Union[None, Coroutine[Any, Any, None]]]] = None,
        worker_threads: int = 4
    ):
        self.recording_file = recording_file
        self.message_callback = message_callback
        self.worker_threads = worker_threads
        self.max_queue_size = 1000
    
    def validate(self) -> None:
        """Validate the simulation configuration."""
        if not self.recording_file:
            raise ValueError("recording_file must be provided")

@dataclass
class MQTTStreamState:
    """Internal state management for MQTT stream."""
    is_running: bool = False
    is_recording: bool = False
    is_replaying: bool = False
    current_topics: List[str] = field(default_factory=list)
    error_state: Optional[str] = None 