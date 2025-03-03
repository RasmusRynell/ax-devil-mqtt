#!/usr/bin/env python3
import click
import asyncio
from pathlib import Path
from ax_devil_mqtt.core.manager import MQTTStreamManager
from ax_devil_mqtt.core.types import SimulatorConfig, MQTTStreamConfig
from ax_devil_device_api import DeviceConfig
from ax_devil_device_api.features.mqtt_client import BrokerConfig

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

@device.command("monitor")
@click.option("--device-ip", required=True, help="IP address of the device")
@click.option("--username", required=True, help="Device username")
@click.option("--password", required=True, help="Device password")
@click.option("--broker", "-b", required=True, help="MQTT broker address")
@click.option("--port", "-p", default=1883, help="MQTT broker port")
@click.option("--streams", "-s", multiple=True, help="Analytics streams to monitor")
@click.option("--record", "-r", is_flag=True, help="Record messages to file")
@click.option("--duration", "-d", default=0, help="Monitoring duration in seconds (0 for infinite)")
def monitor(device_ip, username, password, broker, port, streams, record, duration):
    """Monitor specific analytics streams"""
    device_config = DeviceConfig.http(
        host=device_ip,
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
    
    config = MQTTStreamConfig(
        broker_config=broker_config,
        device_config=device_config,
        analytics_mqtt_data_source_key=streams[0] if streams else None,
        message_callback=default_message_callback
    )
    
    manager = MQTTStreamManager(config)
    
    try:
        manager.start()
        if record:
            Path("recordings").mkdir(exist_ok=True)
            manager.start_recording("recordings/device_recording.jsonl")
        
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
    
    config = MQTTStreamConfig(
        broker_config=broker_config,
        simulator_config=simulator_config,
        message_callback=default_message_callback
    )
    
    manager = MQTTStreamManager(config)
    
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