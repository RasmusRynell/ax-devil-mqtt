import asyncio
import signal
import time
import sys
from datetime import datetime
from pathlib import Path
from ax_devil_mqtt.core.manager import MQTTStreamManager
from ax_devil_mqtt.core.types import SimulatorConfig, MQTTStreamConfig
from ax_devil_device_api.features.mqtt_client import BrokerConfig

# MQTT Broker configuration
BROKER_CONFIG = BrokerConfig(
    host="192.168.1.57",  # Replace with your MQTT broker's IP or hostname
    port=1883,
    use_tls=False,
    clean_session=True,
    auto_reconnect=True
)

# Simulator configuration
SIMULATOR_CONFIG = SimulatorConfig(
    recording_file="recordings/mqtt_recording_20250216_132215.jsonl"
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

class ReplayExample:
    """
    Example demonstrating MQTT message recording and replay functionality.
    
    This class shows how to:
    - Set up a recording session for MQTT messages
    - Replay previously recorded MQTT messages
    - Handle graceful shutdown
    """
    
    def __init__(self):
        self.running = True
        self.manager = None
        
    def setup(self):
        """Initialize MQTT manager with broker and simulator configuration."""
        print(f"Setting up with MQTT config: {BROKER_CONFIG}")
        print(f"Using simulator config: {SIMULATOR_CONFIG}")
        
        # Create recordings directory if it doesn't exist
        Path("recordings").mkdir(exist_ok=True)
        
        config = MQTTStreamConfig(
            broker_config=BROKER_CONFIG,
            simulator_config=SIMULATOR_CONFIG,
            message_callback=message_callback
        )
        
        self.manager = MQTTStreamManager(config)
        
        # Start components (publisher will be started automatically if simulator config is provided)
        self.manager.start()

    async def start_recording(self):
        """
        Start a new recording session.
        
        Returns:
            str: Path to the recording file
        """
        print("Waiting 1 second before starting recording...")
        await asyncio.sleep(1)
        
        # Start recording with timestamp in filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = f"recordings/mqtt_recording_{timestamp}.jsonl"
        
        print(f"Starting recording to {filepath}")
        self.manager.start_recording(filepath)
        time.sleep(10)
        self.manager.stop_recording()
        return filepath

    async def replay_recording(self, recording_file: str):
        """
        Replay messages from a recorded session.
        
        Args:
            recording_file: Path to the JSONL file containing recorded messages
        """
        try:
            print(f"Starting replay of {recording_file}...")
            self.manager.start_replay(recording_file)
            print("Replay started. Messages will be logged via the callback.")
            
            # Keep running until interrupted
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"Error during replay: {e}")
        finally:
            self.manager.stop_replay()

    def signal_handler(self, sig, frame):
        """Handle graceful shutdown on interrupt signal."""
        print("\nStopping example...")
        self.running = False
        self.manager.stop()
        print("\nRecorded messages will be saved in the recordings directory")
        sys.exit(0)

    def run(self):
        """Run the complete example: record messages and replay them."""
        print(f"Starting MQTT Replay Example")
        print(f"MQTT Broker: {BROKER_CONFIG.host}:{BROKER_CONFIG.port}")
        print("-" * 50)
        
        self.setup()
        
        try:
            # Create and run the event loop
            loop = asyncio.get_event_loop()
            
            # Start a new recording
            recording_file = loop.run_until_complete(self.start_recording())
            
            # Start replay of an existing recording
            loop.run_until_complete(
                self.replay_recording(
                    recording_file=SIMULATOR_CONFIG.recording_file
                )
            )
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.manager.stop()

if __name__ == "__main__":
    example = ReplayExample()
    signal.signal(signal.SIGINT, example.signal_handler)
    example.run()