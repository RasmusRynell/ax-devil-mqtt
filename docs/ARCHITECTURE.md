# Architecture

## Overview

The ax-devil-mqtt project is designed as a simple yet effective Python library for managing MQTT communication with Axis devices, with an accompanying CLI for testing and basic operations. The architecture follows a modular design with clear separation of concerns, while avoiding unnecessary complexity.

## Core Components

### 1. DeviceMQTTManager (Core Library)

The central component that orchestrates all functionality:

```python
class DeviceMQTTManager:
    def __init__(self, config: Dict[str, Any]):
        self.broker = None          # Optional internal broker
        self.subscriber = None      # MQTT subscriber (with optional recording)
        self.publisher = None       # MQTT publisher (for simulation/device commands)
        self.device = None          # Axis device interface
        
    def start_recording(self):
        """Enable recording in the subscriber"""
        if self.subscriber:
            self.subscriber.start_recording()
            
    def stop_recording(self):
        """Disable recording in the subscriber"""
        if self.subscriber:
            self.subscriber.stop_recording()
```

Key responsibilities:
- MQTT broker management (optional)
- Subscriber management (with recording capability)
- Publisher management (for simulation/commands)
- Device communication coordination

### 2. Component Structure

The library is organized into simple, focused modules:

```
ax_devil_mqtt/
├── __init__.py
├── manager.py          # DeviceMQTTManager implementation
├── mqtt_broker.py      # Optional internal broker
├── subscriber.py       # MQTT subscriber with recording capability
├── publisher.py        # MQTT publisher for simulation/commands
├── device_interface.py # Axis device communication (<50 lines)
└── cli.py             # Command-line interface
```

## Design Principles

1. **Simplicity First**
   - Each component has a single, clear responsibility
   - Minimal dependencies between components
   - No complex folder hierarchies

2. **Flexible Configuration**
   - Support for both internal and external MQTT brokers
   - Recording built into subscriber
   - Simple device interface that can be extended

3. **Clean Interfaces**
   - Clear separation between publishing and subscribing
   - Recording as an integral part of subscription
   - Type hints for better code clarity

## Flow Patterns

### Normal Operation
1. Manager initializes components based on configuration
2. Subscriber connects to broker and sets up topics
3. Publisher connects (if needed for device commands)
4. Device interface establishes connection
5. Messages flow through MQTT with optional recording in subscriber

### Simulation Mode
1. Manager starts in simulation mode
2. Publisher loads recorded data file
3. Publisher sends messages to broker
4. Normal subscriber receives messages (recording disabled in simulation)

## CLI Design

The CLI provides a simple interface for common operations:

```bash
ax-devil-mqtt [--broker HOST] [--port PORT] [--simulation FILE] [--record]
```

Key features:
- Basic device setup and monitoring
- Recording through subscriber
- Simulation through publisher
- Interactive command mode for manual control

## Dependencies

Core dependencies are kept minimal:
- paho-mqtt: MQTT client functionality
- click: CLI interface (optional)
- ax-devil-conf: Device communication (your simple implementation)
