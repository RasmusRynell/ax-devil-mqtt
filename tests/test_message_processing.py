"""
Tests for message processing functionality that don't require a device.
"""
import time
from ax_devil_mqtt.core.manager import MessageProcessor


def test_message_processor_basic():
    """Test that the MessageProcessor can process messages."""
    processed_messages = []
    def callback(message):
        processed_messages.append(message)
    
    processor = MessageProcessor(callback=callback, worker_threads=1)
    
    test_message = {"topic": "test/topic", "payload": "test_payload"}
    processor.submit_message(test_message)
    
    time.sleep(0.1)
    
    assert len(processed_messages) == 1
    assert processed_messages[0]["payload"] == "test_payload"


def test_message_processor_multiple_messages():
    """Test that the MessageProcessor can handle multiple messages."""
    processed_messages = []
    def callback(message):
        processed_messages.append(message)
    
    processor = MessageProcessor(callback=callback, worker_threads=2)
    
    for i in range(5):
        test_message = {"topic": f"test/topic/{i}", "payload": f"test_payload_{i}"}
        processor.submit_message(test_message)
    
    time.sleep(0.2)
    
    assert len(processed_messages) == 5
    payloads = [msg["payload"] for msg in processed_messages]
    for i in range(5):
        assert f"test_payload_{i}" in payloads


def test_message_processor_error_handling():
    """Test that the MessageProcessor handles errors in callbacks."""
    error_count = 0
    def error_callback(message):
        nonlocal error_count
        error_count += 1
        raise ValueError("Test error")
    
    processor = MessageProcessor(callback=error_callback, worker_threads=1)
    
    test_message = {"topic": "test/topic", "payload": "test_payload"}
    
    processor.submit_message(test_message)
    
    time.sleep(0.1)
    
    assert error_count == 1 