import os
import json
import logging
import pika
import urllib.parse
import ssl
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def get_rabbitmq_connection():
    """
    Establishes and returns a blocking connection to the RabbitMQ server.
    It checks for the 'USE_LOCAL_RABBITMQ' flag and for CloudAMQP settings.
    """
    use_local = os.environ.get("USE_LOCAL_RABBITMQ", "false").lower() == "true"
    if not use_local:
        cloudamqp_url = os.environ.get("CLOUDAMQP_URL")
        if cloudamqp_url:
            url_params = urllib.parse.urlparse(cloudamqp_url)
            credentials = pika.PlainCredentials(url_params.username, url_params.password)
            ssl_context = ssl.create_default_context()
            ssl_options = pika.SSLOptions(context=ssl_context)
            connection_params = pika.ConnectionParameters(
                host=url_params.hostname,
                port=url_params.port or 5671,  # CloudAMQP typically uses 5671 for SSL
                virtual_host=url_params.path[1:] if url_params.path else '/',
                credentials=credentials,
                ssl_options=ssl_options
            )
            logger.info(f"Connecting using CloudAMQP at {url_params.hostname}:{url_params.port or 5671}")
            return pika.BlockingConnection(connection_params)
    # Fallback to local RabbitMQ.
    rabbitmq_host = os.environ.get("RABBITMQ_HOST", "localhost")
    try:
        rabbitmq_port = int(os.environ.get("RABBITMQ_PORT", 5672))
    except ValueError:
        logger.warning("Invalid RABBITMQ_PORT value. Defaulting to 5672.")
        rabbitmq_port = 5672
    connection_params = pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port)
    logger.info(f"Connecting using local RabbitMQ at {rabbitmq_host}:{rabbitmq_port}")
    return pika.BlockingConnection(connection_params)

def publish_order(order: dict, queue_name: str = "orders") -> None:
    """
    Publishes an enriched order to the specified RabbitMQ queue.
    """
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        # Declare the queue with durability so that messages survive RabbitMQ restarts.
        channel.queue_declare(queue=queue_name, durable=True)
        message = json.dumps(order)
        channel.basic_publish(
            exchange="",
            routing_key=queue_name,
            body=message,
            properties=pika.BasicProperties(delivery_mode=2)  # Persistent delivery
        )
        # Process any pending network events to flush the message.
        connection.process_data_events()
        # Sleep briefly to ensure the message is transmitted.
        time.sleep(0.5)
        logger.info(f"Published order: {order.get('order_id')}")
        connection.close()
    except Exception as e:
        logger.error(f"Failed to publish order: {e}")
        raise

__all__ = ["publish_order", "get_rabbitmq_connection"]