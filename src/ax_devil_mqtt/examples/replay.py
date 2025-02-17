import asyncio
import signal
import sys
import argparse
from pathlib import Path
from datetime import datetime
from ax_devil_mqtt.core.manager import MQTTStreamManager
from ax_devil_mqtt.core.types import SimulatorConfig, MQTTStreamConfig
from ax_devil_device_api.features.mqtt_client import BrokerConfig

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Replay MQTT recordings')
    parser.add_argument('recording_path', nargs='?', help='Path to the recording file')
    parser.add_argument('--host', required=True, help='MQTT broker host IP')
    parser.add_argument('--port', type=int, default=1883, help='MQTT broker port (default: 1883)')
    return parser.parse_args()

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
    Example demonstrating MQTT message replay functionality.
    
    This class shows how to:
    - Replay previously recorded MQTT messages
    - Handle graceful shutdown
    """
    
    def __init__(self, recording_path: str = None, broker_host: str = None, broker_port: int = 1883):
        self.running = True
        self.manager = None
        self.recording_path = recording_path
        self.broker_config = BrokerConfig(
            host=broker_host,
            port=broker_port,
            use_tls=False,
            clean_session=True,
            auto_reconnect=True
        )
        
    def setup(self):
        """Initialize MQTT manager with broker and simulator configuration."""
        if not self.recording_path:
            print("Error: No recording file specified!")
            print("\nUsage:")
            print("python src/ax_devil_mqtt/examples/replay.py --host <broker_ip> <recording_file>")
            print("\nTo create a recording first, run:")
            print("python src/ax_devil_mqtt/examples/analytics_monitor.py --host <broker_ip>")
            sys.exit(1)
            
        if not Path(self.recording_path).exists():
            print(f"Error: Recording file {self.recording_path} not found!")
            print("\nTo create a recording first, run:")
            print("python src/ax_devil_mqtt/examples/analytics_monitor.py --host <broker_ip>")
            sys.exit(1)
            
        print(f"Setting up with MQTT broker: {self.broker_config.host}:{self.broker_config.port}")
        print(f"Using recording file: {self.recording_path}")
        
        simulator_config = SimulatorConfig(recording_file=self.recording_path)
        
        config = MQTTStreamConfig(
            broker_config=self.broker_config,
            simulator_config=simulator_config,
            message_callback=message_callback
        )
        
        self.manager = MQTTStreamManager(config)
        self.manager.start()

    async def replay_recording(self):
        """Replay messages from a recorded session."""
        try:
            print(f"Starting replay of {self.recording_path}...")
            self.manager.start_replay(self.recording_path)
            print("Replay started. Messages will be logged via the callback.")
            
            # Keep running until interrupted
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"Error during replay: {e}")
        finally:
            if self.manager:
                self.manager.stop_replay()

    def signal_handler(self, sig, frame):
        """Handle graceful shutdown on interrupt signal."""
        print("\nStopping replay...")
        self.running = False
        if self.manager:
            self.manager.stop()
        sys.exit(0)

    def run(self):
        """Run the replay example."""
        print("Starting MQTT Replay Example")
        print(f"MQTT Broker: {self.broker_config.host}:{self.broker_config.port}")
        print("-" * 50)
        
        self.setup()
        
        try:
            # Create and run the event loop
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.replay_recording())
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            if self.manager:
                self.manager.stop()

if __name__ == "__main__":
    args = parse_args()
    
    example = ReplayExample(
        recording_path=args.recording_path,
        broker_host=args.host,
        broker_port=args.port
    )
    signal.signal(signal.SIGINT, example.signal_handler)
    example.run()