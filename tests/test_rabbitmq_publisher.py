import json
import pika
import pytest
from rabbitmq_publisher import publish_order, get_rabbitmq_connection

@pytest.fixture
def rabbitmq_connection():
    connection = get_rabbitmq_connection()
    yield connection
    connection.close()

def test_publish_order(rabbitmq_connection):
    test_queue = "test_orders"
    channel = rabbitmq_connection.channel()
    channel.queue_declare(queue=test_queue, durable=True)
    channel.queue_purge(queue=test_queue)

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
    
    publish_order(test_order, queue_name=test_queue)
    
    method_frame, header_frame, body = channel.basic_get(queue=test_queue)
    assert method_frame is not None, "No message was published"
    order_received = json.loads(body)
    assert order_received["order_id"] == "TEST123"
    channel.basic_ack(method_frame.delivery_tag)
    channel.queue_purge(queue=test_queue)