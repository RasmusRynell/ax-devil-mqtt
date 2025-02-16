"""
Shared types and configurations for the AX Devil MQTT package.
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class SimulatorConfig:
    """Configuration for MQTT message simulation."""
    recording_file: Optional[str] = None  # Path to recording file for replay 