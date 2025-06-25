from typing import Dict, Any, Union, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
import json

# Message Types

@dataclass
class BaseMessage:
    """Base message class with common fields."""
    topic: str
    payload: Union[str, Dict[str, Any], Any]
    timestamp: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseMessage':
        """Create a BaseMessage from a dictionary."""
        return cls(
            topic=data.get('topic', 'unknown'),
            payload=data.get('payload', ''),
            timestamp=data.get('timestamp', datetime.now().isoformat())
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format."""
        return {
            'topic': self.topic,
            'payload': self.payload,
            'timestamp': self.timestamp
        }

@dataclass
class MQTTMessage(BaseMessage):
    """MQTT-specific message with additional metadata."""
    qos: int = 0
    retain: bool = False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MQTTMessage':
        """Create an MQTTMessage from a dictionary."""
        return cls(
            topic=data.get('topic', 'unknown'),
            payload=data.get('payload', ''),
            timestamp=data.get('timestamp', datetime.now().isoformat()),
            qos=data.get('qos', 0),
            retain=data.get('retain', False)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format."""
        return {
            'topic': self.topic,
            'payload': self.payload,
            'timestamp': self.timestamp,
            'qos': self.qos,
            'retain': self.retain
        }

@dataclass
class AnalyticsMessage(BaseMessage):
    """Analytics-specific message with structured payload."""
    source_key: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalyticsMessage':
        """Create an AnalyticsMessage from a dictionary."""
        return cls(
            topic=data.get('topic', 'unknown'),
            payload=data.get('payload', ''),
            timestamp=data.get('timestamp', datetime.now().isoformat()),
            source_key=data.get('source_key')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format."""
        result = {
            'topic': self.topic,
            'payload': self.payload,
            'timestamp': self.timestamp
        }
        if self.source_key is not None:
            result['source_key'] = self.source_key
        return result

# Replay Statistics

@dataclass
class ReplayStats:
    """Statistics from a replay session."""
    total_drift: float
    max_drift: float
    message_count: int
    avg_drift: float
    
    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'ReplayStats':
        """Create ReplayStats from a dictionary."""
        return cls(
            total_drift=data.get('total_drift', 0.0),
            max_drift=data.get('max_drift', 0.0),
            message_count=int(data.get('message_count', 0)),
            avg_drift=data.get('avg_drift', 0.0)
        )
    
    def to_dict(self) -> Dict[str, float]:
        """Convert stats to dictionary format."""
        return {
            'total_drift': self.total_drift,
            'max_drift': self.max_drift,
            'message_count': float(self.message_count),
            'avg_drift': self.avg_drift
        }

# Type aliases for convenience
Message = Union[BaseMessage, MQTTMessage, AnalyticsMessage]

# Callback type definitions  
from typing import Callable
MessageCallback = Callable[[Message], None]
ReplayCompleteCallback = Callable[[ReplayStats], None]

class DataRetriever(ABC):
    """Interface for message handlers (MQTTSubscriber and ReplayHandler)."""
    @abstractmethod
    def start(self) -> None:
        pass
        
    @abstractmethod
    def stop(self) -> None:
        pass 