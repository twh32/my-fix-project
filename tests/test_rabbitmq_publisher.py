import json
import time
import pytest
from rabbitmq_publisher import publish_order, get_rabbitmq_connection

@pytest.fixture
def rabbitmq_connection():
    """
    Create and yield a RabbitMQ connection for tests.
    """
    connection = get_rabbitmq_connection()
    yield connection
    connection.close()

def test_publish_order(rabbitmq_connection):
    """
    Verifies an order is published to RabbitMQ.
    
    Steps:
      1. Declare and purge a test queue.
      2. Publish a test order.
      3. Wait briefly to allow the message to be enqueued.
      4. Retrieve the message from the queue.
      5. Assert that the message contains the expected order ID.
      6. Acknowledge and purge the queue for cleanup.
    """
    test_queue = "test_orders"
    channel = rabbitmq_connection.channel()
    
    # Declare the queue and purge any old messages.
    channel.queue_declare(queue=test_queue, durable=True)
    channel.queue_purge(queue=test_queue)
    
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
    
    # Publish the test order.
    publish_order(test_order, queue_name=test_queue)
    
    # Wait a bit longer (e.g. 2 seconds) to ensure the message is enqueued.
    time.sleep(2)
    
    # Retrieve the message.
    method_frame, header_frame, body = channel.basic_get(queue=test_queue, auto_ack=False)
    assert method_frame is not None, "No message was published to the queue."
    
    # Verify the contents of the message.
    order_received = json.loads(body)
    assert order_received.get("order_id") == "TEST123", "Order ID does not match the test order."
    
    # Acknowledge the message and purge the queue.
    channel.basic_ack(method_frame.delivery_tag)
    channel.queue_purge(queue=test_queue)