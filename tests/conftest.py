"""
Pytest configuration and fixtures for ax-devil-mqtt tests.
"""
import json
import pytest
from datetime import datetime, timedelta


@pytest.fixture
def sample_message():
    """Return a sample MQTT message for testing."""
    return {
        "topic": "test/topic",
        "payload": "test_payload",
        "timestamp": datetime.now().isoformat()
    }


@pytest.fixture
def sample_recording_file(tmp_path):
    """Create a sample recording file with multiple messages."""
    recording_file = tmp_path / "sample_recording.jsonl"
    
    # Create messages with timestamps 1 second apart
    base_time = datetime.now()
    messages = [
        {
            "topic": f"test/topic/{i}",
            "payload": f"test_payload_{i}",
            "timestamp": (base_time + timedelta(seconds=i)).isoformat()
        }
        for i in range(5)
    ]
    
    # Write messages to file
    with open(recording_file, 'w') as f:
        for msg in messages:
            f.write(json.dumps(msg) + '\n')
    
    return recording_file 