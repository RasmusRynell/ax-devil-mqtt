#!/usr/bin/env python3
import time
from typing import Callable

import click
from ax_devil_device_api import Client, DeviceConfig

from ax_devil_mqtt.core.manager import AxisAnalyticsMqttClient, RawMqttClient
from ax_devil_mqtt.core.types import MqttMessage
from ax_devil_mqtt import __version__

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


def default_message_callback(message: MqttMessage) -> None:
    """Default message callback that echoes the message payload."""
    click.echo(message.payload)


def build_device_config(device_ip: str, device_username: str, device_password: str) -> DeviceConfig:
    """Create a DeviceConfig from CLI-provided credentials."""
    return DeviceConfig.http(host=device_ip, username=device_username, password=device_password)


def device_options(func: Callable) -> Callable:
    """Decorator to add common device options to commands."""
    func = click.option(
        "--device-password",
        "-p",
        envvar="AX_DEVIL_TARGET_PASS",
        show_envvar=True,
        required=True,
        help="Password for authentication",
    )(func)
    func = click.option(
        "--device-username",
        "-u",
        envvar="AX_DEVIL_TARGET_USER",
        show_envvar=True,
        required=True,
        help="Username for authentication",
    )(func)
    func = click.option(
        "--device-ip",
        "-a",
        envvar="AX_DEVIL_TARGET_ADDR",
        show_envvar=True,
        required=True,
        help="Device IP address or hostname",
    )(func)
    return func


@click.group(context_settings=CONTEXT_SETTINGS)
def cli() -> None:
    """AX Devil MQTT Command Line Interface."""
    pass


@cli.command("help", context_settings=CONTEXT_SETTINGS, help="Show help for a command")
@click.pass_context
@click.argument("command", required=False)
def help_command(ctx: click.Context, command: str | None) -> None:
    """Show help for a specific command or the full CLI."""
    if not command:
        click.echo(ctx.parent.get_help() if ctx.parent else cli.get_help(ctx))
        return

    cmd = cli.get_command(ctx, command)
    if cmd is None:
        click.echo(f"Unknown command '{command}'.")
        ctx.exit(1)

    cmd_ctx = click.Context(cmd, info_name=command, parent=ctx.parent)
    click.echo(cmd.get_help(cmd_ctx))


@cli.command("version", help="Show ax-devil-mqtt version", context_settings=CONTEXT_SETTINGS)
def version() -> None:
    """Show the installed version of ax-devil-mqtt."""
    click.echo(__version__)


@cli.command("open-api", help="Open the device API in browser", context_settings=CONTEXT_SETTINGS)
@device_options
def open_api(device_ip: str, device_username: str, device_password: str) -> None:
    """Open the device API."""
    device_config = build_device_config(device_ip, device_username, device_password)

    client = Client(device_config)
    apis = client.discovery.discover()
    analytics_api = apis.get_api("analytics-mqtt")

    import webbrowser
    webbrowser.open(f"https://{device_ip}{analytics_api.rest_ui_url}")


@cli.command("clean", help="Clean existing temporary MQTT publishers", context_settings=CONTEXT_SETTINGS)
@device_options
def clean(device_ip: str, device_username: str, device_password: str) -> None:
    """Clean all temporary MQTT publishers."""
    device_config = build_device_config(device_ip, device_username, device_password)

    client = Client(device_config)
    for publisher in client.analytics_mqtt.list_publishers():
        topic = publisher.get("mqtt_topic")
        publisher_id = publisher.get("id")
        if topic.startswith("ax-devil/temp/"):
            click.echo(f"Deleting publisher {topic} ({publisher_id})")
            client.analytics_mqtt.remove_publisher(publisher_id)


@cli.command("list-publishers", help="List all existing analytics MQTT publishers", context_settings=CONTEXT_SETTINGS)
@device_options
def list_publishers(device_ip: str, device_username: str, device_password: str) -> int | None:
    """List analytics MQTT publishers on the device."""
    device_config = build_device_config(device_ip, device_username, device_password)

    client = Client(device_config)
    try:
        publishers = client.analytics_mqtt.list_publishers()
        if not publishers:
            click.echo("No analytics MQTT publishers found")
            return 0

        click.echo("Analytics MQTT Publishers:")
        for pub in publishers:
            click.echo(
                f"- id: {pub.get('id')}, topic: {pub.get('mqtt_topic')}, data_source_key: {pub.get('data_source_key')}"
            )
    except Exception as e:  # noqa: BLE001
        click.echo(f"Error listing publishers: {e}")


@cli.command("list-sources", help="List available analytics data sources", context_settings=CONTEXT_SETTINGS)
@device_options
def list_sources(device_ip: str, device_username: str, device_password: str) -> int | None:
    """List available analytics data sources from the device."""
    device_config = build_device_config(device_ip, device_username, device_password)

    client = Client(device_config)

    try:
        result = client.analytics_mqtt.get_data_sources()

        if not result:
            click.echo("No analytics data sources available")
            return 0

        click.echo("Available Analytics Data Sources:")
        for source in result:
            click.echo(f"  - {source.get('key')}")
    except Exception as e:  # noqa: BLE001
        click.echo(f"Error listing data sources: {e}")
        click.echo("Make sure the device supports analytics and you have proper credentials.")


@cli.command("subscribe", help="Subscribe to raw MQTT topics", context_settings=CONTEXT_SETTINGS)
@click.option(
    "--broker-address",
    "-b",
    envvar="AX_DEVIL_MQTT_BROKER_ADDR",
    show_envvar=True,
    required=True,
    help="MQTT broker address",
)
@click.option(
    "--broker-port",
    "-P",
    default=1883,
    show_default=True,
    type=click.IntRange(1, 65535),
    help="MQTT broker port",
)
@click.option("--broker-username", "-U", default="", help="MQTT broker username")
@click.option(
    "--broker-password",
    "-W",
    default="",
    envvar="AX_DEVIL_MQTT_BROKER_PASS",
    show_envvar=True,
    help="MQTT broker password",
)
@click.option(
    "--topic",
    "-t",
    required=True,
    help="Raw MQTT topic to subscribe to",
)
def subscribe(
    broker_address: str,
    broker_port: int,
    broker_username: str,
    broker_password: str,
    topic: str,
) -> None:
    """Subscribe to a raw MQTT topic and print messages."""
    mqtt_client: RawMqttClient | None = None
    try:
        mqtt_client = RawMqttClient(
            broker_host=broker_address,
            broker_port=broker_port,
            topics=[topic],
            message_callback=default_message_callback,
            worker_threads=1,
            broker_username=broker_username,
            broker_password=broker_password,
        )
        mqtt_client.start()

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        click.echo("\nStopping subscription...")
    finally:
        if mqtt_client:
            mqtt_client.stop()


@cli.command("monitor", help="Monitor a specific analytics stream", context_settings=CONTEXT_SETTINGS)
@device_options
@click.option(
    "--broker-address",
    "-b",
    envvar="AX_DEVIL_MQTT_BROKER_ADDR",
    show_envvar=True,
    required=True,
    help="MQTT broker address",
)
@click.option(
    "--broker-port",
    "-P",
    default=1883,
    show_default=True,
    type=click.IntRange(1, 65535),
    help="MQTT broker port",
)
@click.option("--broker-username", "-U", default="", help="MQTT broker username")
@click.option(
    "--broker-password",
    "-W",
    default="",
    envvar="AX_DEVIL_MQTT_BROKER_PASS",
    show_envvar=True,
    help="MQTT broker password",
)
@click.option("--stream", "-s", required=True, help="Analytics stream to monitor")
@click.option(
    "--duration",
    "-d",
    default=0,
    show_default=True,
    type=click.IntRange(min=0),
    help="Monitoring duration in seconds (0 for infinite)",
)
def monitor(
    device_ip: str,
    device_username: str,
    device_password: str,
    broker_address: str,
    broker_port: int,
    broker_username: str,
    broker_password: str,
    stream: str,
    duration: int,
) -> None:
    """Monitor a specific analytics stream."""
    if broker_address == "localhost":
        click.echo(
            "Error: Cannot use localhost as broker host since camera has to be configured. Find your IP and use that."
        )
        raise click.Abort()

    device_config = build_device_config(device_ip, device_username, device_password)
    analytics_client: AxisAnalyticsMqttClient | None = None

    try:
        analytics_client = AxisAnalyticsMqttClient(
            broker_host=broker_address,
            broker_port=broker_port,
            device_config=device_config,
            analytics_data_source_key=stream,
            message_callback=default_message_callback,
            worker_threads=1,
            broker_username=broker_username,
            broker_password=broker_password,
        )
        analytics_client.start()

        if duration > 0:
            time.sleep(duration)
        else:
            while True:
                time.sleep(0.1)
    except KeyboardInterrupt:
        click.echo("\nStopping monitoring...")
    finally:
        if analytics_client:
            analytics_client.stop()


if __name__ == "__main__":
    cli()
