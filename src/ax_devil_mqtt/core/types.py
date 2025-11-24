from typing import Any, Callable, Dict
from dataclasses import dataclass

@dataclass
class MqttMessage:
    """Single message type used throughout the package."""
    topic: str
    payload: str
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
