#!/usr/bin/env python3
import click
import asyncio
import os
from pathlib import Path
from ax_devil_mqtt.core.manager import ReplayManager, AnalyticsManager
from ax_devil_device_api import Client, DeviceConfig

async def default_message_callback(message):
    """Default callback to print received messages."""
    print(f"Topic: {message['topic']}")
    print(f"Data: {message['payload']}")
    print("-" * 50)

@click.group()
def cli():
    """AX Devil MQTT - Device Analytics Tool"""
    pass

@cli.group()
def device():
    """Commands for interacting with live devices"""
    pass

@device.command("open-api", help="Open the device API in browser")
@click.option("--device-ip", default=lambda: os.getenv('AX_DEVIL_TARGET_ADDR'),
                     required=False, help='Device IP address or hostname')
@click.option("--username", default=lambda: os.getenv('AX_DEVIL_TARGET_USER'),
                     required=False, help='Username for authentication')
@click.option("--password", default=lambda: os.getenv('AX_DEVIL_TARGET_PASS'),
                     required=False, help='Password for authentication')
def open_api(device_ip, username, password):
    """Open the device API"""
    assert device_ip != None, "Device IP is required, supply or set AX_DEVIL_TARGET_ADDR environment variable"
    assert username != None, "Username is required, supply or set AX_DEVIL_TARGET_USER environment variable"
    assert password != None, "Password is required, supply or set AX_DEVIL_TARGET_PASS environment variable"

    device_config = DeviceConfig.http(
        host=device_ip,
        username=username,
        password=password
    )

    client = Client(device_config)
    apis = client.discovery.discover()
    analytics_api = apis.get_api("analytics-mqtt")

    import webbrowser
    webbrowser.open(f"https://{device_ip}{analytics_api.rest_ui_url}")


@device.command("clean", help="Clean all temporary MQTT publishers")
@click.option("--device-ip", default=lambda: os.getenv('AX_DEVIL_TARGET_ADDR'),
                     required=False, help='Device IP address or hostname')
@click.option("--username", default=lambda: os.getenv('AX_DEVIL_TARGET_USER'),
                     required=False, help='Username for authentication')
@click.option("--password", default=lambda: os.getenv('AX_DEVIL_TARGET_PASS'),
                     required=False, help='Password for authentication')
def clean(device_ip, username, password): 
    """Clean all temporary MQTT publishers"""
    device_config = DeviceConfig.http(
        host=device_ip,
        username=username,
        password=password
    )
    
    client = Client(device_config)
    for publisher in client.analytics_mqtt.list_publishers():
        topic = publisher.get("mqtt_topic")
        id = publisher.get("id")
        if topic.startswith("ax-devil/temp/"):
            print(f"Deleting publisher {topic} ({id})")
            client.analytics_mqtt.remove_publisher(id)

@device.command("monitor", help="Monitor a specific analytics stream")
@click.option("--device-ip", default=lambda: os.getenv('AX_DEVIL_TARGET_ADDR'),
                     required=False, help='Device IP address or hostname')
@click.option("--username", default=lambda: os.getenv('AX_DEVIL_TARGET_USER'),
                     required=False, help='Username for authentication')
@click.option("--password", default=lambda: os.getenv('AX_DEVIL_TARGET_PASS'),
                     required=False, help='Password for authentication')
@click.option("--broker", "-b", required=True, help="MQTT broker address")
@click.option("--port", "-p", default=1883, help="MQTT broker port")
@click.option("--stream", "-s", required=True, help="Analytics stream to monitor")
@click.option("--record", "-r", is_flag=True, help="Record messages to file")
@click.option("--duration", "-d", default=0, help="Monitoring duration in seconds (0 for infinite)")
@click.option("--record-file", "-f", default="recordings/device_recording.jsonl", help="File to record messages to")
def monitor(device_ip, username, password, broker, port, stream, record, duration, record_file):
    """Monitor a specific analytics stream"""
    assert broker != "localhost", "Cannot use localhost as broker host since camera has to be configured. Find your ip and use that."

    assert device_ip != None, "Device IP is required, supply or set AX_DEVIL_TARGET_ADDR environment variable"
    assert username != None, "Username is required, supply or set AX_DEVIL_TARGET_USER environment variable"
    assert password != None, "Password is required, supply or set AX_DEVIL_TARGET_PASS environment variable"

    device_config = DeviceConfig.http(
        host=device_ip,
        username=username,
        password=password
    )
    
    manager = AnalyticsManager(
        broker_host=broker,
        broker_port=port,
        device_config=device_config,
        analytics_data_source_key=stream,
        message_callback=default_message_callback
    )
    
    try:
        if record:
            Path("recordings").mkdir(exist_ok=True)
            manager.start(record_file)
        else:
            manager.start()
        
        if duration > 0:
            asyncio.get_event_loop().run_until_complete(asyncio.sleep(duration))
        else:
            # Run indefinitely until Ctrl+C
            asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print("\nStopping monitoring...")
    finally:
        manager.stop()

@cli.group()
def replay():
    """Commands for replay and replay"""
    pass

@replay.command("replay")
@click.argument("recording_file")
def replay(recording_file):
    """Replay a recorded analytics session"""
    
    loop = asyncio.get_event_loop()
    
    def on_replay_complete():
        print("\nReplay completed. Exiting...")
        loop.call_soon_threadsafe(loop.stop)
    
    manager = ReplayManager(
        recording_file=recording_file,
        message_callback=default_message_callback
    )
    
    if hasattr(manager._handler, 'set_completion_callback'):
        manager._handler.set_completion_callback(on_replay_complete)
    
    try:
        manager.start()
        # Run until the replay is complete or interrupted
        loop.run_forever()
    except KeyboardInterrupt:
        print("\nStopping replay...")
    finally:
        manager.stop()

if __name__ == "__main__":
    cli() 