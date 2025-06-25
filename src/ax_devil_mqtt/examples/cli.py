#!/usr/bin/env python3
import click
import asyncio
import os
from pathlib import Path
from ax_devil_mqtt.core.manager import ReplayManager, AnalyticsManager
from ax_devil_mqtt.core.types import Message, ReplayStats
from ax_devil_device_api import Client, DeviceConfig

async def default_message_callback(message: Message):
    """Default callback to print received messages with strong typing."""
    click.echo(f"Topic: {message.topic}")
    click.echo(f"Data: {message.payload}")
    click.echo("-" * 50)

def validate_device_credentials(device_ip, username, password):
    """Validate that all required device credentials are provided."""
    if device_ip is None:
        click.echo("Error: Device IP is required. Supply --device-ip or set AX_DEVIL_TARGET_ADDR environment variable")
        raise click.Abort()
    if username is None:
        click.echo("Error: Username is required. Supply --username or set AX_DEVIL_TARGET_USER environment variable")
        raise click.Abort()
    if password is None:
        click.echo("Error: Password is required. Supply --password or set AX_DEVIL_TARGET_PASS environment variable")
        raise click.Abort()

def create_device_config(device_ip, username, password):
    """Create a DeviceConfig after validating credentials."""
    validate_device_credentials(device_ip, username, password)
    return DeviceConfig.http(
        host=device_ip,
        username=username,
        password=password
    )

def device_options(func):
    """Decorator to add common device options to commands."""
    func = click.option("--password", default=lambda: os.getenv('AX_DEVIL_TARGET_PASS'),
                       required=False, help='Password for authentication')(func)
    func = click.option("--username", default=lambda: os.getenv('AX_DEVIL_TARGET_USER'),
                       required=False, help='Username for authentication')(func)
    func = click.option("--device-ip", default=lambda: os.getenv('AX_DEVIL_TARGET_ADDR'),
                       required=False, help='Device IP address or hostname')(func)
    return func

@click.group()
def cli():
    """AX Devil MQTT - Device Analytics Tool"""
    pass

@cli.group()
def device():
    """Commands for interacting with live devices"""
    pass

@device.command("open-api", help="Open the device API in browser")
@device_options
def open_api(device_ip, username, password):
    """Open the device API"""
    device_config = create_device_config(device_ip, username, password)

    client = Client(device_config)
    apis = client.discovery.discover()
    analytics_api = apis.get_api("analytics-mqtt")

    import webbrowser
    webbrowser.open(f"https://{device_ip}{analytics_api.rest_ui_url}")


@device.command("clean", help="Clean all temporary MQTT publishers")
@device_options
def clean(device_ip, username, password): 
    """Clean all temporary MQTT publishers"""
    device_config = create_device_config(device_ip, username, password)
    
    client = Client(device_config)
    for publisher in client.analytics_mqtt.list_publishers():
        topic = publisher.get("mqtt_topic")
        id = publisher.get("id")
        if topic.startswith("ax-devil/temp/"):
            click.echo(f"Deleting publisher {topic} ({id})")
            client.analytics_mqtt.remove_publisher(id)

@device.command("list-sources", help="List available analytics data sources")
@device_options
def list_sources(device_ip, username, password):
    """List available analytics data sources from the device"""
    device_config = create_device_config(device_ip, username, password)
    
    client = Client(device_config)
    
    # List available analytics data sources
    try:
        result = client.analytics_mqtt.get_data_sources()

        if not result:
            click.echo("No analytics data sources available")
            return 0
                
        click.echo("Available Analytics Data Sources:")
        for source in result:
            click.echo(f"  - {source.get('key')}")
    except Exception as e:
        click.echo(f"Error listing data sources: {e}")
        click.echo("Make sure the device supports analytics and you have proper credentials.")

@device.command("monitor", help="Monitor a specific analytics stream")
@device_options
@click.option("--broker", "-b", required=True, help="MQTT broker address")
@click.option("--port", "-p", default=1883, help="MQTT broker port")
@click.option("--stream", "-s", required=True, help="Analytics stream to monitor")
@click.option("--record", "-r", is_flag=True, help="Record messages to file")
@click.option("--duration", "-d", default=0, help="Monitoring duration in seconds (0 for infinite)")
@click.option("--record-file", "-f", default="recordings/device_recording.jsonl", help="File to record messages to")
def monitor(device_ip, username, password, broker, port, stream, record, duration, record_file):
    """Monitor a specific analytics stream"""
    if broker == "localhost":
        click.echo("Error: Cannot use localhost as broker host since camera has to be configured. Find your IP and use that.")
        raise click.Abort()
    
    device_config = create_device_config(device_ip, username, password)
    
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
        click.echo("\nStopping monitoring...")
    finally:
        manager.stop()

@cli.command("replay")
@click.argument("recording_file")
def replay(recording_file):
    """Replay a recorded analytics session"""
    
    loop = asyncio.get_event_loop()
    
    def on_replay_complete(stats: ReplayStats):
        click.echo(f"\nReplay completed!")
        click.echo(f"  Total messages: {stats.message_count}")
        click.echo(f"  Average drift: {stats.avg_drift:.2f}ms")
        click.echo(f"  Max drift: {stats.max_drift:.2f}ms")
        click.echo("Exiting...")
        loop.call_soon_threadsafe(loop.stop)
    
    manager = ReplayManager(
        recording_file=recording_file,
        message_callback=default_message_callback,
        on_replay_complete=on_replay_complete
    )
    
    try:
        manager.start()
        # Run until the replay is complete or interrupted
        loop.run_forever()
    except KeyboardInterrupt:
        click.echo("\nStopping replay...")
    finally:
        manager.stop()

if __name__ == "__main__":
    cli() 