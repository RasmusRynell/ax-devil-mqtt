"""
Tests for the simplified single Message type.
"""
from ax_devil_mqtt.core.types import MqttMessage, MessageCallback

class TestMessage:
    """Test Message functionality."""
    
    def test_creation_with_mqtt_fields(self):
        """Test message creation with QoS and retain."""
        msg = MqttMessage(
            topic="mqtt/topic",
            payload={"temperature": 22.5},
            qos=2,
            retain=True
        )
        
        assert msg.topic == "mqtt/topic"
        assert msg.payload == {"temperature": 22.5}
        assert msg.qos == 2
        assert msg.retain is True
    
    def test_to_dict(self):
        """Test message dict conversion includes all fields."""
        msg = MqttMessage(
            topic="mqtt/topic",
            payload="payload",
            qos=1,
            retain=False
        )
        
        msg_dict = msg.to_dict()
        
        assert msg_dict["topic"] == "mqtt/topic"
        assert msg_dict["payload"] == "payload"
        assert msg_dict["qos"] == 1
        assert msg_dict["retain"] is False
        assert "timestamp" not in msg_dict


class TestMessageCallback:
    """Test that message callback typing works."""
    
    def test_message_callback_typing(self):
        received_messages = []
        
        def callback(msg: MqttMessage) -> None:
            received_messages.append(msg)
        
        typed_callback: MessageCallback = callback
        
        typed_callback(MqttMessage("topic1", "payload1"))
        typed_callback(MqttMessage("topic2", "payload2"))
        
        assert len(received_messages) == 2
        assert received_messages[0].topic == "topic1"
        assert received_messages[1].topic == "topic2"
