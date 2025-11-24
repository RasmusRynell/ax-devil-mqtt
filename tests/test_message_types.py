"""
Tests for the message type system and type conversions.
These tests verify the new strongly-typed message classes work correctly.
"""
import pytest
from datetime import datetime

from ax_devil_mqtt.core.types import (
    BaseMessage, MQTTMessage, AnalyticsMessage, Message
)


class TestBaseMessage:
    """Test BaseMessage functionality."""
    
    def test_creation(self):
        """Test basic message creation."""
        msg = BaseMessage(
            topic="test/topic",
            payload="test payload",
            timestamp="2024-01-01T00:00:00Z"
        )
        
        assert msg.topic == "test/topic"
        assert msg.payload == "test payload"
        assert msg.timestamp == "2024-01-01T00:00:00Z"
    
    def test_dict_conversion(self):
        """Test conversion to/from dictionary."""
        original = BaseMessage(
            topic="test/topic",
            payload={"key": "value"},
            timestamp="2024-01-01T00:00:00Z"
        )
        
        # Convert to dict and back
        msg_dict = original.to_dict()
        recreated = BaseMessage.from_dict(msg_dict)
        
        assert recreated.topic == original.topic
        assert recreated.payload == original.payload
        assert recreated.timestamp == original.timestamp
    
    def test_from_dict_with_defaults(self):
        """Test from_dict with missing fields uses defaults."""
        msg = BaseMessage.from_dict({})
        
        assert msg.topic == "unknown"
        assert msg.payload == ""
        assert msg.timestamp is not None  # Should get default timestamp


class TestMQTTMessage:
    """Test MQTTMessage functionality."""
    
    def test_creation_with_mqtt_fields(self):
        """Test MQTT message creation with QoS and retain."""
        msg = MQTTMessage(
            topic="mqtt/topic",
            payload={"temperature": 22.5},
            timestamp="2024-01-01T00:00:00Z",
            qos=2,
            retain=True
        )
        
        assert msg.topic == "mqtt/topic"
        assert msg.payload == {"temperature": 22.5}
        assert msg.qos == 2
        assert msg.retain is True
    
    def test_dict_conversion_includes_mqtt_fields(self):
        """Test MQTT message dict conversion includes all fields."""
        original = MQTTMessage(
            topic="mqtt/topic",
            payload="payload",
            timestamp="2024-01-01T00:00:00Z",
            qos=1,
            retain=False
        )
        
        msg_dict = original.to_dict()
        recreated = MQTTMessage.from_dict(msg_dict)
        
        assert recreated.topic == original.topic
        assert recreated.qos == original.qos
        assert recreated.retain == original.retain
    
    def test_mqtt_defaults(self):
        """Test MQTT message defaults."""
        msg = MQTTMessage(
            topic="test",
            payload="test",
            timestamp="2024-01-01T00:00:00Z"
        )
        
        assert msg.qos == 0
        assert msg.retain is False


class TestAnalyticsMessage:
    """Test AnalyticsMessage functionality."""
    
    def test_creation_with_source_key(self):
        """Test analytics message with source key."""
        msg = AnalyticsMessage(
            topic="analytics/motion",
            payload={"detected": True, "confidence": 0.95},
            timestamp="2024-01-01T00:00:00Z",
            source_key="motion_sensor_1"
        )
        
        assert msg.topic == "analytics/motion"
        assert msg.source_key == "motion_sensor_1"
        assert msg.payload["confidence"] == 0.95
    
    def test_dict_conversion_with_source_key(self):
        """Test analytics message dict conversion includes source_key."""
        original = AnalyticsMessage(
            topic="analytics/topic",
            payload={"data": "value"},
            timestamp="2024-01-01T00:00:00Z",
            source_key="sensor_123"
        )
        
        msg_dict = original.to_dict()
        assert "source_key" in msg_dict
        assert msg_dict["source_key"] == "sensor_123"
        
        recreated = AnalyticsMessage.from_dict(msg_dict)
        assert recreated.source_key == original.source_key
    
    def test_dict_conversion_without_source_key(self):
        """Test analytics message without source_key excludes it from dict."""
        original = AnalyticsMessage(
            topic="analytics/topic",
            payload={"data": "value"},
            timestamp="2024-01-01T00:00:00Z"
        )
        
        msg_dict = original.to_dict()
        assert "source_key" not in msg_dict
        
        recreated = AnalyticsMessage.from_dict(msg_dict)
        assert recreated.source_key is None


class TestMessageUnion:
    """Test Message union type functionality."""
    
    def test_message_types_are_compatible(self):
        """Test that all message types work with Message union."""
        base_msg: Message = BaseMessage("topic", "payload", "2024-01-01T00:00:00Z")
        mqtt_msg: Message = MQTTMessage("topic", "payload", "2024-01-01T00:00:00Z")
        analytics_msg: Message = AnalyticsMessage("topic", "payload", "2024-01-01T00:00:00Z")
        
        # All should have common interface
        assert base_msg.topic == "topic"
        assert mqtt_msg.topic == "topic"
        assert analytics_msg.topic == "topic"
    
    def test_message_callback_typing(self):
        """Test that message callback works with all message types."""
        from ax_devil_mqtt.core.types import MessageCallback
        
        received_messages = []
        
        def callback(msg: Message) -> None:
            received_messages.append(msg)
        
        # Verify callback is properly typed
        typed_callback: MessageCallback = callback
        
        # Test with different message types
        typed_callback(BaseMessage("topic1", "payload1", "2024-01-01T00:00:00Z"))
        typed_callback(MQTTMessage("topic2", "payload2", "2024-01-01T00:00:00Z"))
        typed_callback(AnalyticsMessage("topic3", "payload3", "2024-01-01T00:00:00Z"))
        
        assert len(received_messages) == 3
        assert received_messages[0].topic == "topic1"
        assert received_messages[1].topic == "topic2"
        assert received_messages[2].topic == "topic3" 
