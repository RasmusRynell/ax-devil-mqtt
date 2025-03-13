import asyncio
import signal
import sys
import argparse
import os
from pathlib import Path
from datetime import datetime
from ax_devil_mqtt.core.manager import MQTTStreamManager
from ax_devil_mqtt.core.types import SimulationConfig

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Replay MQTT recordings')
    parser.add_argument('recording_path', help='Path to the recording file')
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
    
    def __init__(self, recording_path: str = None):
        self.running = True
        self.manager = None
        self.recording_path = recording_path
        
    def setup(self):
        """Set up the replay manager with the recording file."""
        if not os.path.exists(self.recording_path):
            print(f"Error: Recording file {self.recording_path} not found!")
            print("\nTo create a recording first, run:")
            print("python src/ax_devil_mqtt/examples/analytics_monitor.py --host <broker_ip>")
            sys.exit(1)
            
        print(f"Using recording file: {self.recording_path}")
        
        config = SimulationConfig(
            recording_file=self.recording_path,
            message_callback=message_callback
        )
        
        self.manager = MQTTStreamManager(config)
        
        def on_replay_complete():
            print("\nReplay completed. Exiting...")
            self.running = False
            
        if hasattr(self.manager._handler, 'set_completion_callback'):
            self.manager._handler.set_completion_callback(on_replay_complete)

    async def replay_recording(self):
        """Replay messages from a recorded session."""
        try:
            print(f"Starting replay of {self.recording_path}...")
            self.manager.start()
            print("Replay started. Messages will be logged via the callback.")
            
            # Keep running until replay completes or is interrupted
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"Error during replay: {e}")
        finally:
            if self.manager:
                self.manager.stop()

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
        recording_path=args.recording_path
    )
    signal.signal(signal.SIGINT, example.signal_handler)
    example.run()