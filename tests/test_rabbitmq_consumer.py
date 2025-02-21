import json
import os
import logging
import pika
import urllib.parse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_rabbitmq_connection():
    """
    Establishes and returns a blocking connection to the RabbitMQ server.
    It first checks for the 'CLOUDAMQP_URL' environment variable, and if present,
    it uses that. Otherwise, it falls back to using RABBITMQ_HOST and RABBITMQ_PORT.
    """
    cloudamqp_url = os.environ.get("CLOUDAMQP_URL")
    if cloudamqp_url:
        # Parse the URL to get connection parameters.
        url_params = urllib.parse.urlparse(cloudamqp_url)
        credentials = pika.PlainCredentials(url_params.username, url_params.password)
        connection_params = pika.ConnectionParameters(
            host=url_params.hostname,
            port=url_params.port or 5671,  # CloudAMQP often uses 5671 for SSL
            virtual_host=url_params.path[1:] if url_params.path else '/',
            credentials=credentials,
            ssl=True  # Enable SSL for CloudAMQP
        )
    else:
        rabbitmq_host = os.environ.get("RABBITMQ_HOST", "localhost")
        try:
            rabbitmq_port = int(os.environ.get("RABBITMQ_PORT", 5672))
        except ValueError:
            logger.warning("Invalid RABBITMQ_PORT value. Defaulting to 5672.")
            rabbitmq_port = 5672
        connection_params = pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port)
    return pika.BlockingConnection(connection_params)

def process_order(order: dict):
    """
    Processes the order. For now, just log the order.
    """
    logger.info(f"Processing order: {order['order_id']}")

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
            logger.error(f"Error processing order: {e}")
            # Optionally, reject or requeue the message:
            # ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    channel.basic_consume(queue=queue_name, on_message_callback=callback)
    logger.info("Starting consumer. Waiting for messages...")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
        connection.close()

if __name__ == '__main__':
    start_order_consumer()