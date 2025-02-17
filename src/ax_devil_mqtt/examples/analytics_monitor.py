import asyncio
import signal
import sys
import argparse
import os
from ax_devil_mqtt.core.manager import MQTTStreamManager
from ax_devil_mqtt.core.types import MQTTStreamConfig
from ax_devil_mqtt.core.publisher import MQTTPublisher
import json
import time
from datetime import datetime
from ax_devil_device_api import CameraConfig
from ax_devil_device_api.features.mqtt_client import BrokerConfig

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Record MQTT analytics data from camera')
    parser.add_argument('--host', required=True, help='MQTT broker host IP')
    parser.add_argument('--port', type=int, default=1883, help='MQTT broker port (default: 1883)')
    parser.add_argument('--duration', type=int, default=10, help='Recording duration in seconds (default: 10)')
    return parser.parse_args()

# Camera configuration
CAMERA_CONFIG = CameraConfig.http(
    host=os.getenv("AXIS_TARGET_ADDR"),
    username=os.getenv("AXIS_TARGET_USER"),
    password=os.getenv("AXIS_TARGET_PASS")
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
    
    def __init__(self, broker_host: str, broker_port: int = 1883, duration: int = 10):
        self.running = True
        self.manager = None
        self.publisher = None
        self.duration = duration
        self.broker_config = BrokerConfig(
            host=broker_host,
            port=broker_port,
            use_tls=False,
            clean_session=True,
            auto_reconnect=True
        )

    def setup(self):
        """Initialize MQTT stream manager and start monitoring analytics."""
        print(f"Setting up manager with camera config: {CAMERA_CONFIG}")
        print(f"Using MQTT broker: {self.broker_config.host}:{self.broker_config.port}")

        # Use analytics data source key for camera mode
        analytics_key = "com.axis.analytics_scene_description.v0.beta#1"
        print(f"Using analytics data source: {analytics_key}")
    
        config = MQTTStreamConfig(
            camera_config=CAMERA_CONFIG,
            broker_config=self.broker_config,
            analytics_mqtt_data_source_key=analytics_key,
            message_callback=message_callback
        )
        
        self.manager = MQTTStreamManager(config)
        self.manager.start()

    async def timed_recording(self):
        """
        Handle timed recording sequence.
        
        Records MQTT messages for specified duration and saves them to a timestamped file
        in the recordings directory.
        
        Returns:
            str: Path to the recording file
        """
        print("Waiting 1 second before starting recording...")
        await asyncio.sleep(1)
        
        # Start recording with timestamp in filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = f"recordings/mqtt_recording_{timestamp}.jsonl"
        os.makedirs("recordings", exist_ok=True)
        
        print(f"Starting recording to {filepath}")
        self.manager.start_recording(filepath)
        
        print(f"Recording for {self.duration} seconds...")
        await asyncio.sleep(self.duration)
        
        print("Stopping recording")
        self.manager.stop_recording()
        
        print("\nRecording completed!")
        print(f"To replay this recording, run:")
        print(f"python src/ax_devil_mqtt/examples/replay.py --host {self.broker_config.host} {filepath}")
        
        return filepath

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
        print(f"MQTT Broker: {self.broker_config.host}:{self.broker_config.port}")
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
    args = parse_args()
    
    example = CameraExample(
        broker_host=args.host,
        broker_port=args.port,
        duration=args.duration
    )
    signal.signal(signal.SIGINT, example.signal_handler)
    example.run()
