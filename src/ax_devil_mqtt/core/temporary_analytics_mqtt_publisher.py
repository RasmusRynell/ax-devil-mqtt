from ax_devil_device_api import Client, DeviceConfig
import uuid
import sys
import logging

logger = logging.getLogger(__name__)

class TemporaryAnalyticsMQTTPublisher:
    """Automatic temporary MQTT analytics publisher setup and cleanup."""
    
    def __init__(self, 
                 device_config: DeviceConfig,
                 broker_host: str,
                 broker_port: int,
                 topic: str,
                 client_id: str,
                 analytics_data_source_key: str = "com.axis.analytics_scene_description.v0.beta#1",
                 broker_username: str = "",
                 broker_password: str = ""):
        self.client = Client(device_config)
        self._cleanup_done = False
        self._publisher_created = False
        
        self._analytics_publisher_id = None
        self._initial_mqtt_status = None

        self._initial_mqtt_status = self.client.mqtt_client.get_state()

        try:
            self.client.mqtt_client.configure(
                host=broker_host,
                port=broker_port,
                username=broker_username,
                password=broker_password,
                client_id=client_id
            )

            self._publisher_created = self._setup_analytics_publisher(analytics_data_source_key, topic)

            self.client.mqtt_client.activate()
        
        except Exception as e:
            self._restore_device_state()
            raise RuntimeError(f"Failed to configure analytics publisher: {e}")
        
    def _restore_device_state(self) -> None:
        """
        Restore the device to its original MQTT state.
        This removes any publishers we created and restores the original MQTT configuration.
        """
        try:
            # Remove any analytics publishers we created
            if self._publisher_created and self._analytics_publisher_id:
                self.client.analytics_mqtt.remove_publisher(self._analytics_publisher_id)

            # Restore MQTT state
            if self._initial_mqtt_status and self._initial_mqtt_status["config"]:
                self.client.mqtt_client.set_state(self._initial_mqtt_status["config"])
            if self._initial_mqtt_status["status"]["state"] == "active":
                self.client.mqtt_client.activate()
            else:
                self.client.mqtt_client.deactivate()
        except Exception as e:
            raise RuntimeError(f"Error during device state restoration: {e}")

    def _setup_analytics_publisher(self, analytics_data_source_key: str, topic: str) -> bool:
        """Create or reuse an existing analytics publisher on the device.
            returns true if created, false if reused"""

        publishers = self.client.analytics_mqtt.list_publishers()
        for publisher in publishers:
            if (publisher.get("mqtt_topic") == topic and 
                publisher.get("data_source_key") == analytics_data_source_key and 
                publisher.get("qos") == 0 and 
                not publisher.get("retain") and 
                not publisher.get("use_topic_prefix")):
                self._analytics_publisher_id = publisher.get("id")
                return False # publisher already exists

        self._analytics_publisher_id = str(uuid.uuid4())        
        self.client.analytics_mqtt.create_publisher(
                        id=self._analytics_publisher_id,
                        data_source_key=analytics_data_source_key,
                        mqtt_topic=topic,
                        qos=0,
                        retain=False,
                        use_topic_prefix=False
        )
        return True # publisher created

    def cleanup(self):
        """Clean up resources and restore the device to its original state."""
        if self._cleanup_done:
            return
            
        try:
            self._restore_device_state()
            self._cleanup_done = True
            self.client.close()
        except Exception as e:
            logger.warning(f"Warning: Error during cleanup: {e}")

    def __del__(self):
        """Ensure cleanup when object is destroyed."""
        if not self._cleanup_done and sys and sys.modules:
            self.cleanup()
        self.client.close()
