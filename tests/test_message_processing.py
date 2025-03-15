"""
Tests for message processing functionality that don't require a device.
"""
import time
import threading
import pytest
from ax_devil_mqtt.core.manager import MessageProcessor


def test_message_processor_basic():
    """Test that the MessageProcessor can process messages."""
    # Create a simple callback to capture messages
    processed_messages = []
    def callback(message):
        processed_messages.append(message)
    
    # Initialize the processor
    processor = MessageProcessor(callback=callback, worker_threads=1)
    
    # Process a message
    test_message = {"topic": "test/topic", "payload": "test_payload"}
    processor.submit_message(test_message)
    
    # Wait briefly for processing to complete
    time.sleep(0.1)
    
    # Verify message was processed
    assert len(processed_messages) == 1
    assert processed_messages[0]["payload"] == "test_payload"


def test_message_processor_multiple_messages():
    """Test that the MessageProcessor can handle multiple messages."""
    # Create a simple callback to capture messages
    processed_messages = []
    def callback(message):
        processed_messages.append(message)
    
    # Initialize the processor
    processor = MessageProcessor(callback=callback, worker_threads=2)
    
    # Process multiple messages
    for i in range(5):
        test_message = {"topic": f"test/topic/{i}", "payload": f"test_payload_{i}"}
        processor.submit_message(test_message)
    
    # Wait briefly for processing to complete
    time.sleep(0.2)
    
    # Verify all messages were processed
    assert len(processed_messages) == 5
    # Messages might be processed in any order due to threading
    payloads = [msg["payload"] for msg in processed_messages]
    for i in range(5):
        assert f"test_payload_{i}" in payloads


def test_message_processor_error_handling():
    """Test that the MessageProcessor handles errors in callbacks."""
    # Create a callback that raises an exception
    error_count = 0
    def error_callback(message):
        nonlocal error_count
        error_count += 1
        raise ValueError("Test error")
    
    # Initialize the processor
    processor = MessageProcessor(callback=error_callback, worker_threads=1)
    
    # Process a message
    test_message = {"topic": "test/topic", "payload": "test_payload"}
    
    # The processor should catch the exception and log it
    # We can't easily test the logging, but we can verify it doesn't crash
    processor.submit_message(test_message)
    
    # Wait briefly for processing to complete
    time.sleep(0.1)
    
    # Verify the callback was called
    assert error_count == 1 