from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from ax_devil_device_api import Client, DeviceConfig
from ax_devil_device_api.features.mqtt_client import BrokerConfig, MqttStatus
from ax_devil_device_api.features.analytics_mqtt import PublisherConfig, DataSource
import uuid
import sys

@dataclass
class AnalyticsMQTTConfiguration:
    """Current configuration and status of the analytics MQTT stream."""
    mqtt_status: MqttStatus
    mqtt_broker: Dict[str, Any]
    analytics_sources: List[DataSource]
    analytics_publishers: List[PublisherConfig]

class DeviceAnalyticsMQTTManager:
    """
    Manages device-side MQTT analytics publishers with automatic lifecycle management.
    
    This class provides a high-level interface for:
    - Setting up MQTT broker connections on the device
    - Creating and configuring analytics publishers on the device
    - Managing the lifecycle of publishers (creation and cleanup)
    - Restoring the device's original state when done
    
    It uses the ax_devil library for all device interactions and maintains
    state to ensure proper cleanup when the manager is destroyed.
    """
    
    def __init__(self, 
                 device_config: DeviceConfig,
                 broker_config: BrokerConfig,
                 topic: str = "analytics",
                 analytics_data_source_key: str = "com.axis.analytics_scene_description.v0.beta#1"):
        """
        Initialize analytics manager with device and MQTT configuration.
        
        Args:
            device_config: DeviceConfig instance for device connection
            broker_config: BrokerConfig instance for MQTT broker settings
            topic: Base topic for analytics messages
            analytics_data_source_key: Analytics data source identifier
            
        Raises:
            RuntimeError: If setup or mqtt client setup fails
        """
        self.client = Client(device_config)
        self._cleanup_done = False
        
        self._analytics_publisher_id = None
        self._initial_mqtt_status = None
        self.topics = None
        
        self._capture_mqtt_current_state()
        
        result = self.client.mqtt_client.configure(broker_config)
        if not result.is_success:
            raise RuntimeError(f"Failed to configure MQTT broker: {result.error}")

        if not self._setup_analytics_publisher(analytics_data_source_key, topic, broker_config.device_topic_prefix or ""):
            self._restore_device_state()
            raise RuntimeError("Failed to configure analytics publisher")

        if self._initial_mqtt_status.state != MqttStatus.STATE_ACTIVE:
            result = self.client.mqtt_client.activate()
            if not result.is_success:
                self._restore_device_state()
                raise RuntimeError(f"Failed to activate MQTT client: {result.error}")

    def _capture_mqtt_current_state(self) -> MqttStatus:
        """
        Capture the current MQTT state of the device.
        This is used to restore the device to its original state when the manager is destroyed.
        
        Returns:
            MqttStatus containing current MQTT state
        """
        mqtt_client_status = self.client.mqtt_client.get_status()
        if not mqtt_client_status.is_success:
            raise RuntimeError(f"Failed to get MQTT status: {mqtt_client_status.error}, check if device is online and reachable")
        self._initial_mqtt_status = mqtt_client_status.data

    def _restore_device_state(self) -> None:
        """
        Restore the device to its original MQTT state.
        This removes any publishers we created and restores the original MQTT configuration.
        """
        try:
            # Remove any analytics publishers we created
            if self._analytics_publisher_id:
                self.client.analytics_mqtt.remove_publisher(self._analytics_publisher_id)

            # Restore MQTT state
            if self._initial_mqtt_status and self._initial_mqtt_status.config:
                self.client.mqtt_client.configure(self._initial_mqtt_status.config)
                if self._initial_mqtt_status.state == MqttStatus.STATE_ACTIVE:
                    self.client.mqtt_client.activate()
            else:
                self.client.mqtt_client.deactivate()
        except Exception as e:
            raise RuntimeError(f"Error during device state restoration: {e}")

    def _setup_analytics_publisher(self, analytics_data_source_key: str, topic: str, custom_topic_prefix: str = "") -> bool:
        """
        Set up an analytics publisher on the device.
        This either finds an existing compatible publisher or creates a new one.
        
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
        if not publishers.is_success:
            return False

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
        return result.is_success

    def cleanup(self):
        """
        Clean up resources and restore the device to its original state.
        This should be called when the manager is no longer needed.
        """
        if self._cleanup_done:
            return
            
        try:
            self._restore_device_state()
            self._cleanup_done = True
        except Exception as e:
            print(f"Warning: Error during cleanup: {e}")

    def __del__(self):
        """Ensure cleanup when object is destroyed."""
        if not self._cleanup_done and sys and sys.modules:
            self.cleanup()
        self.client.close()
