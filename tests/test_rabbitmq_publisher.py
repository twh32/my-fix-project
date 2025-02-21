import json
import pika
import pytest
from rabbitmq_publisher import publish_order, get_rabbitmq_connection

@pytest.fixture
def rabbitmq_connection():
    """
    Pytest fixture to create and later close a RabbitMQ connection.
    """
    connection = get_rabbitmq_connection()
    yield connection
    connection.close()

def test_publish_order(rabbitmq_connection):
    """
    Test that verifies an order is successfully published to RabbitMQ.
    It:
      1. Declares and purges a test queue.
      2. Publishes a test order.
      3. Retrieves the message from the queue.
      4. Asserts that the message contains the expected order ID.
      5. Acknowledges and purges the queue.
    """
    test_queue = "test_orders"
    channel = rabbitmq_connection.channel()
    
    # Ensure the test queue exists and is empty.
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
    
    # Retrieve the message from the queue.
    method_frame, header_frame, body = channel.basic_get(queue=test_queue)
    assert method_frame is not None, "No message was published to the queue."
    
    order_received = json.loads(body)
    assert order_received["order_id"] == "TEST123", "Order ID does not match the test order."
    
    # Acknowledge the message and purge the queue for cleanup.
    channel.basic_ack(method_frame.delivery_tag)
    channel.queue_purge(queue=test_queue)