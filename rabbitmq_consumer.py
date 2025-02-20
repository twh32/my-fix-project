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

def process_order(order: dict):
    """
    Processes the order. For now, just log the order.
    """
    logging.info(f"Processing order: {order['order_id']}")

def start_order_consumer(queue_name: str = "orders"):
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)

    def callback(ch, method, properties, body):
        try:
            order = json.loads(body)
            process_order(order)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logging.error(f"Error processing order: {e}")
            # Optionally, reject or requeue the message:
            # ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    channel.basic_consume(queue=queue_name, on_message_callback=callback)
    logging.info("Starting consumer. Waiting for messages...")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
        connection.close()

if __name__ == '__main__':
    start_order_consumer()

__all__ = ["process_order"]