from typing import Dict, Any, Union, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class MqttMessage:
    """Single message type used throughout the package."""
    topic: str
    payload: Union[str, Dict[str, Any], Any]
    qos: int = 0
    retain: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format."""
        return {
            'topic': self.topic,
            'payload': self.payload,
            'qos': self.qos,
            'retain': self.retain
        }

MessageCallback = Callable[[MqttMessage], None]
class DataRetriever(ABC):
    """Interface for message handlers such as MQTTSubscriber."""
    @abstractmethod
    def start(self) -> None:
        pass
        
    @abstractmethod
    def stop(self) -> None:
        pass 
