import argparse
import signal
import sys
import threading
from ax_devil_mqtt.core.manager import ReplayManager

def main():
    """Run the MQTT replay example."""
    parser = argparse.ArgumentParser(description='Replay MQTT recordings')
    parser.add_argument('recording_path', help='Path to the recording file')
    args = parser.parse_args()
    
    # Create an event to signal when replay is complete
    replay_complete = threading.Event()
    
    def on_replay_complete():
        print("\nReplay completed!")
        replay_complete.set()
    
    def message_callback(message):
        print(message)

    # Create the replay manager
    manager = ReplayManager(
        recording_file=args.recording_path,
        message_callback=message_callback,
        on_replay_complete=on_replay_complete
    )
    
    # Set up signal handler for graceful shutdown
    def signal_handler(sig, frame):
        print("\nStopping replay...")
        manager.stop()
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)
    
    print(f"Starting replay of {args.recording_path}...")
    manager.start()
    print("Replay started. Messages will be printed as they arrive.")
    
    try:
        while not replay_complete.wait(0.5):
            pass
    except Exception as e:
        print(f"Error: {e}")
    finally:
        manager.stop()

if __name__ == "__main__":
    main()