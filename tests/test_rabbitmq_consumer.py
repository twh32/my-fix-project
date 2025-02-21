import json
import time
import threading
import pytest
import logging
import pika
from rabbitmq_consumer import get_rabbitmq_connection, start_order_consumer

# Define a test order for our purposes.
TEST_QUEUE = "test_orders"
TEST_ORDER = {
    "order_id": "TEST_CONSUMER",
    "symbol": "TEST",
    "quantity": 10,
    "price": 100.0,
    "business_unit": "BU-TEST",
    "trader_id": "TRADER_TEST",
    "risk_category": "LOW",
    "processed_timestamp": "2025-02-18T00:00:00Z"
}

@pytest.fixture(scope="function")
def publish_test_order():
    # Connect to RabbitMQ, declare the test queue, purge it, and publish our test order.
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    channel.queue_declare(queue=TEST_QUEUE, durable=True)
    channel.queue_purge(queue=TEST_QUEUE)
    
    # Publish the test order.
    message = json.dumps(TEST_ORDER)
    channel.basic_publish(
        exchange="",
        routing_key=TEST_QUEUE,
        body=message,
        properties=pika.BasicProperties(delivery_mode=2)
    )
    connection.close()
    # Return the order so tests can reference it if needed.
    return TEST_ORDER

def test_consumer_process_order(caplog, publish_test_order):
    """
    Test that the consumer picks up a message from RabbitMQ and processes it.
    We capture log output and assert that the expected processing message is logged.
    """
    # Start the consumer in a separate thread using the test queue.
    def run_consumer():
        try:
            # start_order_consumer will connect to RabbitMQ and begin consuming from TEST_QUEUE.
            start_order_consumer(queue_name=TEST_QUEUE)
        except Exception as e:
            logging.error(f"Consumer error: {e}")

    consumer_thread = threading.Thread(target=run_consumer, daemon=True)
    consumer_thread.start()

    # Give the consumer a few seconds to process the message.
    time.sleep(3)

    # Stop the consumer thread gracefully.
    # (Since our consumer code runs indefinitely, in real tests you might want to
    #  have a mechanism to stop it. Here we rely on daemon threads so that they exit when the test ends.)

    # Check the logs captured by caplog for our expected message.
    expected_log = f"Processing order: {publish_test_order.get('order_id')}"
    assert any(expected_log in record.message for record in caplog.records), \
        "Consumer did not process the order as expected."