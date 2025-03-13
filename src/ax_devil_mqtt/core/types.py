from typing import Dict
from abc import ABC, abstractmethod

class DataRetriever(ABC):
    """Interface for message handlers (MQTTSubscriber and ReplayHandler)."""
    @abstractmethod
    def start(self) -> None:
        pass
        
    @abstractmethod
    def stop(self) -> None:
        pass 