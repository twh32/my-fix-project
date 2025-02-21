import os
import json
import logging
import pika

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def get_rabbitmq_connection():
    """
    Establishes and returns a blocking connection to the RabbitMQ server.
    It first checks for a CloudAMQP URL; if found, it uses that.
    Otherwise, it falls back to using RABBITMQ_HOST and RABBITMQ_PORT.

    Environment Variables:
        CLOUDAMQP_URL: Full AMQP URL (e.g., amqps://user:pass@host/vhost)
        RABBITMQ_HOST (default: "localhost")
        RABBITMQ_PORT (default: 5672)

    Returns:
        pika.BlockingConnection: An active connection to the RabbitMQ server.
    """
    cloudamqp_url = os.environ.get("CLOUDAMQP_URL")
    if cloudamqp_url:
        try:
            connection_params = pika.URLParameters(cloudamqp_url)
            logger.info("Connecting using CLOUDAMQP_URL")
            return pika.BlockingConnection(connection_params)
        except Exception as e:
            logger.error(f"Failed to connect using CLOUDAMQP_URL: {e}")
            raise
    else:
        rabbitmq_host = os.environ.get("RABBITMQ_HOST", "localhost")
        try:
            rabbitmq_port = int(os.environ.get("RABBITMQ_PORT", 5672))
        except ValueError:
            logger.warning("Invalid RABBITMQ_PORT value. Defaulting to 5672.")
            rabbitmq_port = 5672

        connection_params = pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port)
        logger.info(f"Connecting using RABBITMQ_HOST={rabbitmq_host} and RABBITMQ_PORT={rabbitmq_port}")
        return pika.BlockingConnection(connection_params)

def publish_order(order: dict, queue_name: str = "orders") -> None:
    """
    Publishes an enriched order to the specified RabbitMQ queue.

    The function:
      1. Establishes a connection to RabbitMQ.
      2. Declares the queue (durable).
      3. Serializes the order dictionary to JSON.
      4. Publishes the message with persistent delivery mode.
      5. Closes the connection after publishing.

    Args:
        order (dict): The enriched order data to be published.
        queue_name (str, optional): The name of the RabbitMQ queue. Defaults to "orders".

    Raises:
        Exception: Propagates any exceptions encountered during publishing.
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
            properties=pika.BasicProperties(delivery_mode=2)  # Message persistence
        )
        logger.info(f"Published order: {order.get('order_id')}")
        connection.close()
    except Exception as e:
        logger.error(f"Failed to publish order: {e}")
        raise

__all__ = ["publish_order", "get_rabbitmq_connection"]