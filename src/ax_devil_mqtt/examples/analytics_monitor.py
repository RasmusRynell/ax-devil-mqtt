import argparse
import signal
import sys
import os
import time
from datetime import datetime
from ax_devil_mqtt.core.manager import AnalyticsManager
from ax_devil_device_api import DeviceConfig

def main():
    """Run the MQTT analytics monitoring example."""
    parser = argparse.ArgumentParser(description='Record MQTT analytics data from device')
    parser.add_argument('--host', required=True, help='MQTT broker host IP')
    parser.add_argument('--port', type=int, default=1883, help='MQTT broker port (default: 1883)')
    parser.add_argument('--duration', type=int, default=10, help='Recording duration in seconds (default: 10)')
    parser.add_argument('--analytics-key', required=False, help='Analytics stream to monitor', default="com.axis.analytics_scene_description.v0.beta#1")
    args = parser.parse_args()
    
    # Validate broker host
    if args.host == "localhost":
        print("Error: Cannot use localhost as broker host since camera has to be configured.")
        print("Find your IP address and use that instead.")
        sys.exit(1)
    
    device_config = DeviceConfig.http(
        host=os.getenv("AX_DEVIL_TARGET_ADDR"),
        username=os.getenv("AX_DEVIL_TARGET_USER"),
        password=os.getenv("AX_DEVIL_TARGET_PASS")
    )
    
    if not device_config.host or not device_config.username or not device_config.password:
        print("Error: Device IP, username, or password not set. Please set AX_DEVIL_TARGET_ADDR, AX_DEVIL_TARGET_USER, and AX_DEVIL_TARGET_PASS environment variables.")
        sys.exit(1)
    
    # Define message callback
    def message_callback(message):
        """Print received MQTT messages."""
        print(f"Topic: {message['topic']}")
        print(f"Data: {message['payload']}")
        print("-" * 50)
    
    # Create the analytics manager
    print(f"Setting up connection to device: {device_config.host}")
    print(f"Using MQTT broker: {args.host}:{args.port}")
    
    print(f"Using analytics data source key: {args.analytics_key}")
    
    manager = AnalyticsManager(
        broker_host=args.host,
        broker_port=args.port,
        device_config=device_config,
        analytics_data_source_key=args.analytics_key,
        message_callback=message_callback
    )
    
    # Set up signal handler for graceful shutdown
    def signal_handler(sig, frame):
        print("\nStopping analytics monitor...")
        manager.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Create recording file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = f"recordings/mqtt_analytics_recording_{timestamp}.jsonl"
    
    print(f"Starting recording to {filepath}")
    manager.start(recording_file=filepath)
    
    print(f"Recording for {args.duration} seconds...")
    try:
        for remaining in range(args.duration, 0, -1):
            print(f"Time remaining: {remaining} seconds", end="\r")
            time.sleep(1)
        print("\nRecording complete!                ")
    except KeyboardInterrupt:
        print("\nRecording interrupted by user")
    finally:
        manager.stop()
        
    print(f"\nRecording saved to: {filepath}")
    print(f"To replay this recording, run:")
    print(f"python -m ax_devil_mqtt.examples.replay {filepath}")

if __name__ == "__main__":
    main()
