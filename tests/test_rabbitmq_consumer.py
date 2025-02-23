import json
import time
import threading
import pytest
import logging

import pika
from rabbitmq_consumer import get_rabbitmq_connection, start_order_consumer

# Define a test order and queue
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
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    channel.queue_declare(queue=TEST_QUEUE, durable=True)
    channel.queue_purge(queue=TEST_QUEUE)
    message = json.dumps(TEST_ORDER)
    channel.basic_publish(
        exchange="",
        routing_key=TEST_QUEUE,
        body=message,
        properties=pika.BasicProperties(delivery_mode=2)
    )
    connection.close()
    return TEST_ORDER

def test_consumer_process_order(publish_test_order):
    processed_orders = []
    consumer_thread = threading.Thread(
        target=lambda: start_order_consumer(queue_name=TEST_QUEUE, processed_orders=processed_orders),
        daemon=True
    )
    consumer_thread.start()

    # Give the consumer enough time to process the message.
    time.sleep(5)

    expected_order_id = publish_test_order.get("order_id")
    assert any(order.get("order_id") == expected_order_id for order in processed_orders), \
        "Consumer did not process the order as expected."