import asyncio
import signal
import sys
from ax_devil_mqtt.core.manager import MQTTStreamManager
from ax_devil_mqtt.core.types import MQTTStreamConfig
from ax_devil_mqtt.core.publisher import MQTTPublisher
import os
import json
import time
from datetime import datetime
from ax_devil_device_api import CameraConfig
from ax_devil_device_api.features.mqtt_client import BrokerConfig

# Camera configuration
CAMERA_CONFIG = CameraConfig.http(
    host=os.getenv("AXIS_TARGET_ADDR"),
    username=os.getenv("AXIS_TARGET_USER"),
    password=os.getenv("AXIS_TARGET_PASS")
)

# MQTT Broker configuration
BROKER_CONFIG = BrokerConfig(
    host="192.168.1.57",
    port=1883,
    use_tls=False,
    clean_session=True,
    auto_reconnect=True
)

async def message_callback(message):
    """
    Handle MQTT messages by printing topic and payload.
    
    Args:
        message: Dictionary containing 'topic' and 'payload' keys
    """
    try:
        print(f"Topic: {message['topic']}")
        print(f"Data: {message['payload']}")
        print("-" * 50)
    except Exception as e:
        print(f"Error processing message: {e}")

class CameraExample:
    """
    Example demonstrating camera MQTT integration and message recording.
    
    This class shows how to:
    - Set up a connection to an Axis camera
    - Configure MQTT message publishing
    - Record MQTT messages for a specified duration
    - Handle graceful shutdown
    """
    
    def __init__(self):
        self.running = True
        self.manager = None
        self.publisher = None

    def setup(self):
        """Initialize MQTT stream manager and start monitoring analytics."""
        print(f"Setting up manager with camera config: {CAMERA_CONFIG}")
        print(f"Also using MQTT config: {BROKER_CONFIG}")

        # Use analytics data source key for camera mode
        analytics_key = "com.axis.analytics_scene_description.v0.beta#1"
        print(f"Using analytics data source: {analytics_key}")
    
        config = MQTTStreamConfig(
            camera_config=CAMERA_CONFIG,
            broker_config=BROKER_CONFIG,
            analytics_mqtt_data_source_key=analytics_key,
            message_callback=message_callback
        )
        
        self.manager = MQTTStreamManager(config)
        
        # Start the manager
        self.manager.start()

    async def timed_recording(self):
        """
        Handle timed recording sequence.
        
        Records MQTT messages for 10 seconds and saves them to a timestamped file
        in the recordings directory.
        """
        print("Waiting 1 second before starting recording...")
        await asyncio.sleep(1)
        
        # Start recording with timestamp in filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = f"recordings/mqtt_recording_{timestamp}.jsonl"
        os.makedirs("recordings", exist_ok=True)
        
        print(f"Starting recording to {filepath}")
        self.manager.start_recording(filepath)
        
        print("Recording for 10 seconds...")
        await asyncio.sleep(10)
        
        print("Stopping recording")
        self.manager.stop_recording()

    def signal_handler(self, sig, frame):
        """Handle graceful shutdown on interrupt signal."""
        print("\nStopping camera monitor...")
        self.running = False
        
        if self.manager:
            self.manager.stop()
            
        sys.exit(0)

    def run(self):
        """Run the camera example with timed recording."""
        print(f"Camera IP: {CAMERA_CONFIG.host}")
        print(f"MQTT Broker: {BROKER_CONFIG.host}")
        print("-" * 50)
        
        self.setup()
        
        try:
            # Create and run the event loop
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.timed_recording())
            
            # Continue running after recording is complete
            while self.running:
                loop.run_until_complete(asyncio.sleep(1))
        except Exception as e:
            print(f"Error: {e}")
        finally:
            if self.manager:
                self.manager.stop()

if __name__ == "__main__":
    example = CameraExample()
    signal.signal(signal.SIGINT, example.signal_handler)
    example.run()
