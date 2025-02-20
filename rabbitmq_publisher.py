import pika
import json
import os
import logging

logging.basicConfig(level=logging.INFO)

def get_rabbitmq_connection():
    rabbitmq_host = os.environ.get("RABBITMQ_HOST", "localhost")
    rabbitmq_port = int(os.environ.get("RABBITMQ_PORT", 5672))
    connection_params = pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port)
    return pika.BlockingConnection(connection_params)

def publish_order(order: dict, queue_name: str = "orders"):
    """
    Publishes an enriched order to the RabbitMQ queue.
    """
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        channel.queue_declare(queue=queue_name, durable=True)
        message = json.dumps(order)
        channel.basic_publish(
            exchange="",
            routing_key=queue_name,
            body=message,
            properties=pika.BasicProperties(delivery_mode=2)
        )
        logging.info(f"Published order: {order['order_id']}")
        connection.close()
    except Exception as e:
        logging.error(f"Failed to publish order: {e}")
        raise

__all__ = ["publish_order", "get_rabbitmq_connection"]