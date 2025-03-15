"""
Basic sanity check tests for ax-devil-mqtt that don't require a physical device.
These tests verify that core components can be imported and basic functionality works.
"""
import os
import json
import time
import pytest
from datetime import datetime

from ax_devil_mqtt.core.recorder import Recorder
from ax_devil_mqtt.core.replay import ReplayHandler


def test_recorder_functionality(tmp_path):
    """Test that the Recorder can write messages to a file."""
    recording_file = tmp_path / "test_recording.jsonl"
    
    recorder = Recorder()
    recorder.start_recording(str(recording_file))
    
    test_message = {
        "topic": "test/topic", 
        "payload": "test_payload", 
        "timestamp": datetime.now().isoformat()
    }
    recorder.record_message(test_message)
    
    recorder.stop_recording()
    
    assert recording_file.exists()
    with open(recording_file, 'r') as f:
        content = f.read()
        assert "test_payload" in content
        assert "test/topic" in content


def test_recorder_start_stop():
    """Test that the Recorder can be started and stopped."""
    recorder = Recorder()
    
    assert not recorder.is_recording()
    
    with pytest.raises(IOError):
        recorder.start_recording("/invalid/path/that/does/not/exist/file.jsonl")
    
    assert not recorder.is_recording()


def test_replay_handler_with_sample_file(tmp_path):
    """Test that the ReplayHandler can read and replay messages from a file."""
    recording_file = tmp_path / "sample_recording.jsonl"
    with open(recording_file, 'w') as f:
        f.write('{"topic": "test/topic", "payload": "test_payload", "timestamp": "2023-01-01T00:00:00Z"}\n')
        f.write('{"topic": "test/topic2", "payload": "test_payload2", "timestamp": "2023-01-01T00:00:01Z"}\n')
    
    received_messages = []
    def callback(message):
        received_messages.append(message)
    
    handler = ReplayHandler(message_callback=callback, recording_file=str(recording_file))
    handler.start()
    
    time.sleep(0.5)
    
    handler.stop()
    
    assert len(received_messages) == 2
    assert received_messages[0] == "test_payload"  # The ReplayHandler returns just the payload
    assert received_messages[1] == "test_payload2"


def test_replay_handler_error_handling():
    """Test that the ReplayHandler handles errors appropriately."""
    handler = ReplayHandler(message_callback=lambda msg: None)
    
    with pytest.raises(ValueError):
        handler.start()
    
    handler = ReplayHandler(
        message_callback=lambda msg: None,
        recording_file="/path/that/does/not/exist.jsonl"
    )
    
    handler.start()
    
    time.sleep(0.1)
    
    assert not handler.is_replaying() 