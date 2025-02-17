#!/usr/bin/env python3
import click
import asyncio
from pathlib import Path
from ax_devil_mqtt.core.manager import MQTTStreamManager, SimulatorConfig
from ax_devil_device_api import CameraConfig
from ax_devil_device_api.features.mqtt_client import BrokerConfig

async def default_message_callback(message):
    """Default callback to print received messages."""
    print(f"Topic: {message['topic']}")
    print(f"Data: {message['payload']}")
    print("-" * 50)

@click.group()
def cli():
    """AX Devil MQTT - Camera Analytics Tool"""
    pass

@cli.group()
def camera():
    """Commands for interacting with live cameras"""
    pass

@camera.command("list-streams")
@click.option("--camera-ip", required=True, help="IP address of the camera")
@click.option("--username", required=True, help="Camera username")
@click.option("--password", required=True, help="Camera password")
def list_streams(camera_ip, username, password):
    """List available analytics streams from the camera"""
    config = CameraConfig.http(
        host=camera_ip,
        username=username,
        password=password
    )
    manager = MQTTStreamManager(camera_config=config)
    streams = manager.get_available_streams()
    for stream in streams:
        print(f"- {stream}")

@camera.command("monitor")
@click.option("--camera-ip", required=True, help="IP address of the camera")
@click.option("--username", required=True, help="Camera username")
@click.option("--password", required=True, help="Camera password")
@click.option("--broker", "-b", required=True, help="MQTT broker address")
@click.option("--port", "-p", default=1883, help="MQTT broker port")
@click.option("--streams", "-s", multiple=True, help="Analytics streams to monitor")
@click.option("--record", "-r", is_flag=True, help="Record messages to file")
@click.option("--duration", "-d", default=0, help="Monitoring duration in seconds (0 for infinite)")
def monitor(camera_ip, username, password, broker, port, streams, record, duration):
    """Monitor specific analytics streams"""
    camera_config = CameraConfig.http(
        host=camera_ip,
        username=username,
        password=password
    )
    
    broker_config = BrokerConfig(
        host=broker,
        port=port,
        use_tls=False,
        clean_session=True,
        auto_reconnect=True
    )
    
    manager = MQTTStreamManager(
        camera_config=camera_config,
        broker_config=broker_config,
        analytics_mqtt_data_source_key=streams[0] if streams else None,
        message_callback=default_message_callback
    )
    
    try:
        manager.start()
        if record:
            Path("recordings").mkdir(exist_ok=True)
            manager.start_recording("recordings/camera_recording.jsonl")
        
        if duration > 0:
            asyncio.get_event_loop().run_until_complete(asyncio.sleep(duration))
        else:
            # Run indefinitely until Ctrl+C
            asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print("\nStopping monitoring...")
    finally:
        if record:
            manager.stop_recording()
        manager.stop()

@cli.group()
def simulation():
    """Commands for simulation and replay"""
    pass

@simulation.command("replay")
@click.argument("recording_file")
@click.option("--broker", "-b", required=True, help="MQTT broker address")
@click.option("--port", "-p", default=1883, help="MQTT broker port")
def replay(recording_file, broker, port):
    """Replay a recorded analytics session"""
    broker_config = BrokerConfig(
        host=broker,
        port=port,
        use_tls=False,
        clean_session=True,
        auto_reconnect=True
    )
    
    simulator_config = SimulatorConfig(
        recording_file=recording_file
    )
    
    manager = MQTTStreamManager(
        broker_config=broker_config,
        simulator_config=simulator_config,
        topics=[],  # Topics will be determined from the recording
        message_callback=default_message_callback
    )
    
    try:
        manager.start()
        # Run until the replay is complete or interrupted
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print("\nStopping replay...")
    finally:
        manager.stop()

if __name__ == "__main__":
    cli() 