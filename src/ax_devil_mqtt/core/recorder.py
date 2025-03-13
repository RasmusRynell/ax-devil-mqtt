"""
Message recorder for saving MQTT messages to files.
"""
import json
import os
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class Recorder:
    """Records messages to a file for later replay."""
    def __init__(self):
        """Initialize the recorder."""
        self._recording_enabled = False
        self._recording_file = None
    
    def record_message(self, message: Dict[str, Any]) -> None:
        """Record a message to file."""
        if self._recording_enabled and self._recording_file:
            try:
                json.dump(message, self._recording_file)
                self._recording_file.write('\n')
                self._recording_file.flush()
            except Exception as e:
                logger.error(f"Error recording message: {e}")
    
    def start_recording(self, filepath: str) -> None:
        """Start recording messages to file."""
        if self._recording_enabled:
            self.stop_recording()
        
        try:
            os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
            
            self._recording_file = open(filepath, 'a')
            self._recording_enabled = True
            logger.info(f"Started recording messages to {filepath}")
        except IOError as e:
            if self._recording_file:
                self._recording_file.close()
                self._recording_file = None
            raise IOError(f"Failed to open recording file: {e}")
    
    def stop_recording(self) -> None:
        """Stop recording and close file."""
        if not self._recording_enabled:
            return
            
        self._recording_enabled = False
        if self._recording_file:
            try:
                self._recording_file.close()
            except Exception as e:
                logger.error(f"Error closing recording file: {e}")
            finally:
                self._recording_file = None
            logger.info("Stopped recording messages")
    
    def is_recording(self) -> bool:
        """Check if currently recording messages."""
        return self._recording_enabled
    
    def __del__(self):
        """Clean up resources."""
        self.stop_recording() 