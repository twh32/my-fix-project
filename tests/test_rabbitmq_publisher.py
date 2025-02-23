import json
import time
import pytest
from rabbitmq_publisher import publish_order, get_rabbitmq_connection

def test_publish_order():
    test_queue = "test_orders"
    
    # First, use a new connection to declare and purge the test queue.
    init_conn = get_rabbitmq_connection()
    init_channel = init_conn.channel()
    init_channel.queue_declare(queue=test_queue, durable=True)
    init_channel.queue_purge(queue=test_queue)
    init_conn.close()

    # Define a test order.
    test_order = {
        "order_id": "TEST123",
        "symbol": "TEST",
        "quantity": 10,
        "price": 99.99,
        "business_unit": "BU-TEST",
        "trader_id": "TRADER_TEST",
        "risk_category": "LOW",
        "processed_timestamp": "2025-02-18T00:00:00Z"
    }
    
    # Publish the test order using the publisher function.
    publish_order(test_order, queue_name=test_queue)
    
    # Wait a short while to ensure the message is enqueued.
    time.sleep(2)
    
    # Create a new connection and channel to retrieve the message.
    check_conn = get_rabbitmq_connection()
    check_channel = check_conn.channel()
    check_channel.queue_declare(queue=test_queue, durable=True)
    
    method_frame, header_frame, body = None, None, None
    for _ in range(5):
        time.sleep(1)
        method_frame, header_frame, body = check_channel.basic_get(queue=test_queue, auto_ack=True)
        if method_frame is not None:
            break

    # Assert that a message was indeed published.
    assert method_frame is not None, "No message was published to the queue."
    
    # Decode and verify the message.
    order_received = json.loads(body)
    assert order_received.get("order_id") == "TEST123", "Order ID does not match the test order."
    
    # Clean up by purging the test queue.
    check_channel.queue_purge(queue=test_queue)
    check_conn.close()