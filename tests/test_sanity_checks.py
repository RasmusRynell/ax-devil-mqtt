"""
Basic sanity check tests for ax-devil-mqtt that don't require a physical device.
These tests verify that core components can be imported and basic functionality works.
"""
import os
import json
import time
import pytest
from datetime import datetime

# Import the components we want to test
from ax_devil_mqtt.core.recorder import Recorder
from ax_devil_mqtt.core.replay import ReplayHandler


def test_imports():
    """Test that all core modules can be imported without errors."""
    # Test that all modules can be imported without errors
    from ax_devil_mqtt.core.manager import RawMQTTManager, AnalyticsManager
    from ax_devil_mqtt.core.subscriber import MQTTSubscriber
    from ax_devil_mqtt.core.replay import ReplayHandler
    from ax_devil_mqtt.core.recorder import Recorder
    from ax_devil_mqtt.core.types import DataRetriever
    from ax_devil_mqtt.core.temporary_analytics_mqtt_publisher import TemporaryAnalyticsMQTTPublisher
    
    # Just assert that the imports worked
    assert RawMQTTManager is not None
    assert AnalyticsManager is not None
    assert MQTTSubscriber is not None
    assert ReplayHandler is not None
    assert Recorder is not None
    assert DataRetriever is not None
    assert TemporaryAnalyticsMQTTPublisher is not None


def test_recorder_functionality(tmp_path):
    """Test that the Recorder can write messages to a file."""
    # Create a temporary file path
    recording_file = tmp_path / "test_recording.jsonl"
    
    # Initialize recorder
    recorder = Recorder()
    recorder.start_recording(str(recording_file))
    
    # Record a simple message
    test_message = {
        "topic": "test/topic", 
        "payload": "test_payload", 
        "timestamp": datetime.now().isoformat()
    }
    recorder.record_message(test_message)
    
    # Stop recording
    recorder.stop_recording()
    
    # Verify file exists and contains the message
    assert recording_file.exists()
    with open(recording_file, 'r') as f:
        content = f.read()
        assert "test_payload" in content
        assert "test/topic" in content


def test_recorder_start_stop():
    """Test that the Recorder can be started and stopped."""
    recorder = Recorder()
    
    # Test initial state
    assert not recorder.is_recording()
    
    # Test with a temporary file
    with pytest.raises(IOError):
        # Should raise an error with an invalid path
        recorder.start_recording("/invalid/path/that/does/not/exist/file.jsonl")
    
    # Verify still not recording after failed start
    assert not recorder.is_recording()


def test_replay_handler_with_sample_file(tmp_path):
    """Test that the ReplayHandler can read and replay messages from a file."""
    # Create a sample recording file
    recording_file = tmp_path / "sample_recording.jsonl"
    with open(recording_file, 'w') as f:
        f.write('{"topic": "test/topic", "payload": "test_payload", "timestamp": "2023-01-01T00:00:00Z"}\n')
        f.write('{"topic": "test/topic2", "payload": "test_payload2", "timestamp": "2023-01-01T00:00:01Z"}\n')
    
    # Create a simple callback to capture messages
    received_messages = []
    def callback(message):
        received_messages.append(message)
    
    # Initialize and run the replay handler
    handler = ReplayHandler(message_callback=callback, recording_file=str(recording_file))
    handler.start()
    
    # Wait briefly for replay to complete
    time.sleep(0.5)
    
    # Stop the handler
    handler.stop()
    
    # Verify messages were received
    assert len(received_messages) == 2
    assert received_messages[0] == "test_payload"  # The ReplayHandler returns just the payload
    assert received_messages[1] == "test_payload2"


def test_replay_handler_error_handling():
    """Test that the ReplayHandler handles errors appropriately."""
    # Test with no recording file
    handler = ReplayHandler(message_callback=lambda msg: None)
    
    # Should raise an error when starting without a recording file
    with pytest.raises(ValueError):
        handler.start()
    
    # Test with non-existent file
    handler = ReplayHandler(
        message_callback=lambda msg: None,
        recording_file="/path/that/does/not/exist.jsonl"
    )
    
    # Start the handler - it will log an error but not raise an exception
    handler.start()
    
    # Wait briefly for the error to be logged
    time.sleep(0.1)
    
    # Verify the handler is not replaying
    assert not handler.is_replaying() 