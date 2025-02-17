from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from ax_devil_device_api import Client, CameraConfig
from ax_devil_device_api.features.mqtt_client import BrokerConfig, MqttStatus
from ax_devil_device_api.features.analytics_mqtt import PublisherConfig, DataSource
import uuid
import atexit
import sys

@dataclass
class AnalyticsMQTTConfiguration:
    """Current configuration and status of the analytics MQTT stream."""
    mqtt_status: MqttStatus
    mqtt_broker: Dict[str, Any]
    analytics_sources: List[DataSource]
    analytics_publishers: List[PublisherConfig]

class TemporaryAnalyticsMQTTDataStream:
    """
    Manages MQTT and analytics configuration for temporary analytics data streams.
    
    This class provides a high-level interface for:
    - Setting up MQTT broker connections
    - Configuring analytics publishers
    - Managing stream state and cleanup
    
    It uses the ax_devil library for all camera interactions and maintains
    state to ensure proper cleanup when the stream is destroyed.
    """
    
    def __init__(self, 
                 camera_config: CameraConfig,
                 broker_config: BrokerConfig,
                 topic: str = "analytics",
                 analytics_data_source_key: str = "com.axis.analytics_scene_description.v0.beta#1"):
        """
        Initialize analytics stream with camera and MQTT configuration.
        
        Args:
            camera_config: CameraConfig instance for camera connection
            broker_config: BrokerConfig instance for MQTT broker settings
            topic: Base topic for analytics messages
            analytics_data_source_key: Analytics data source identifier
            
        Raises:
            RuntimeError: If stream setup or mqtt client setup fails
        """
        self.client = Client(camera_config)
        self._cleanup_done = False
        
        self._initial_mqtt_status = self._capture_mqtt_current_state()
        self._analytics_publisher_id = None
        self.topics = None
        
        result = self.client.mqtt_client.configure(broker_config)
        if not result.success:
            raise RuntimeError(f"Failed to configure MQTT broker: {result.error}")

        if not self._setup_analytics(analytics_data_source_key, topic, broker_config.device_topic_prefix or ""):
            self._restore_state()
            raise RuntimeError("Failed to configure analytics publisher")

        if self._initial_mqtt_status.state != MqttStatus.STATE_ACTIVE:
            result = self.client.mqtt_client.activate()
            if not result.success:
                self._restore_state()
                raise RuntimeError(f"Failed to activate MQTT client: {result.error}")

        # Register cleanup with atexit instead of relying on __del__
        atexit.register(self.cleanup)

    def cleanup(self):
        """Clean up resources and restore state."""
        if self._cleanup_done:
            return
            
        try:
            self._restore_state()
            self._cleanup_done = True
        except Exception as e:
            # Log but don't raise during cleanup
            print(f"Warning: Error during cleanup: {e}")

    def get_current_configuration(self) -> Optional[AnalyticsMQTTConfiguration]:
        """
        Get the current configuration and status of the analytics stream.
        
        Returns:
            AnalyticsMQTTConfiguration if successful, None if any component fails
        """
        try:
            mqtt_status = self.client.mqtt_client.get_status()
            if not mqtt_status.success:
                return None
                
            sources = self.client.analytics_mqtt.get_data_sources()
            if not sources.success:
                return None
                
            publishers = self.client.analytics_mqtt.list_publishers()
            if not publishers.success:
                return None
                
            return AnalyticsMQTTConfiguration(
                mqtt_status=mqtt_status.data,
                mqtt_broker={
                    'host': mqtt_status.data.config.host if mqtt_status.data.config else None,
                    'port': mqtt_status.data.config.port if mqtt_status.data.config else None,
                    'status': mqtt_status.data.state,
                    'connected_to': mqtt_status.data.connected_to
                },
                analytics_sources=sources.data,
                analytics_publishers=publishers.data
            )
        except Exception as e:
            print(f"Failed to get analytics stream configuration: {e}")
            return None

    def _capture_mqtt_current_state(self) -> MqttStatus:
        """
        Capture the current MQTT state.
        
        Returns:
            MqttStatus containing current MQTT state
        """
        mqtt_client_status = self.client.mqtt_client.get_status()
        if not mqtt_client_status.success:
            raise RuntimeError(f"Failed to get MQTT status: {mqtt_client_status.error}")
        return mqtt_client_status.data

    def _restore_state(self) -> None:
        """Restore the analytics stream to its initial state."""
        try:
            # Remove any analytics publishers we created
            if self._analytics_publisher_id:
                self.client.analytics_mqtt.remove_publisher(self._analytics_publisher_id)

            # Restore MQTT state
            if self._initial_mqtt_status.config:
                self.client.mqtt_client.configure(self._initial_mqtt_status.config)
                if self._initial_mqtt_status.state == MqttStatus.STATE_ACTIVE:
                    self.client.mqtt_client.activate()
            else:
                self.client.mqtt_client.deactivate()
        except Exception as e:
            raise RuntimeError(f"Error during state restoration: {e}")

    def _setup_analytics(self, analytics_data_source_key: str, topic: str, custom_topic_prefix: str = "") -> bool:
        """
        Set up analytics publisher configuration.
        
        Args:
            analytics_data_source_key: Analytics data source identifier
            topic: Base topic for analytics messages
            custom_topic_prefix: Optional prefix for MQTT topics
            
        Returns:
            bool: True if setup successful, False otherwise
        """
        our_topic = custom_topic_prefix + topic
        self.topics = [our_topic]

        publishers = self.client.analytics_mqtt.list_publishers()
        if not publishers.success:
            return False

        # Check for existing compatible publisher
        for publisher in publishers.data:
            if (publisher.mqtt_topic == our_topic and 
                publisher.data_source_key == analytics_data_source_key and 
                publisher.qos == 0 and 
                not publisher.retain and 
                not publisher.use_topic_prefix):
                self._analytics_publisher_id = publisher.id
                return True

        # Create new publisher if none exists
        self._analytics_publisher_id = str(uuid.uuid4())
        config = PublisherConfig(
            id=self._analytics_publisher_id,
            data_source_key=analytics_data_source_key,
            mqtt_topic=our_topic,
            qos=0,
            retain=False,
            use_topic_prefix=False
        )
        
        result = self.client.analytics_mqtt.create_publisher(config)
        return result.success

    def __del__(self):
        """Ensure cleanup when object is destroyed."""
        if not self._cleanup_done and sys and sys.modules:
            self.cleanup()


if __name__ == "__main__":
    import os
    from pprint import pprint
    
    try:
        # Example usage with explicit configuration
        camera_config = CameraConfig.http(
            host=os.getenv("AXIS_TARGET_ADDR"),
            username=os.getenv("AXIS_TARGET_USER"),
            password=os.getenv("AXIS_TARGET_PASS"),
        )
        
        broker_config = BrokerConfig(
            host="192.168.1.57",
            port=1883,
            device_topic_prefix="ax_devil_tmp/",
            use_tls=False,
            clean_session=True,
            auto_reconnect=True
        )
        
        device = TemporaryAnalyticsMQTTDataStream(
            camera_config=camera_config,
            broker_config=broker_config,
            analytics_data_source_key="com.axis.analytics_scene_description.v0.beta#1"
        )
        
        # Check configuration
        config = device.get_current_configuration()
        if config:
            print("\nDevice Configuration:")
            print("-" * 50)
            print(f"MQTT Status: {config.mqtt_status.state}")
            print(f"MQTT Broker: {config.mqtt_broker['host']}:{config.mqtt_broker['port']}")
            if config.mqtt_broker['connected_to']:
                print(f"Connected To: {config.mqtt_broker['connected_to']}")
            
            print(f"\nAnalytics Sources: {len(config.analytics_sources)}")
            for source in config.analytics_sources:
                print(f"- {source.name} ({source.key})")
            
            print(f"\nConfigured Publishers: {len(config.analytics_publishers)}")
            for pub in config.analytics_publishers:
                print(f"- {pub.mqtt_topic} <- {pub.data_source_key}")
            
            print("\nSetup Successful!")
            import time
            time.sleep(10)
            sys.exit(0)
        else:
            print("Failed to get device configuration")
            sys.exit(1)
            
    except RuntimeError as e:
        print(f"Setup failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)