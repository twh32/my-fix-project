import json
import os
import logging
import pika
import urllib.parse
import ssl  # Make sure to import ssl if you're using it

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def get_rabbitmq_connection():
    """
    Establishes and returns a blocking connection to the RabbitMQ server.
    It checks for the 'CLOUDAMQP_URL' environment variable and, if found,
    parses it to configure an SSL connection. Otherwise, it uses RABBITMQ_HOST and RABBITMQ_PORT.
    """
    cloudamqp_url = os.environ.get("CLOUDAMQP_URL")
    if cloudamqp_url:
        url_params = urllib.parse.urlparse(cloudamqp_url)
        credentials = pika.PlainCredentials(url_params.username, url_params.password)
        ssl_context = ssl.create_default_context()
        ssl_options = pika.SSLOptions(context=ssl_context)
        connection_params = pika.ConnectionParameters(
            host=url_params.hostname,
            port=url_params.port or 5671,
            virtual_host=url_params.path[1:] if url_params.path else '/',
            credentials=credentials,
            ssl_options=ssl_options
        )
        logger.info(f"Connecting using CloudAMQP at {url_params.hostname}:{url_params.port or 5671}")
    else:
        rabbitmq_host = os.environ.get("RABBITMQ_HOST", "localhost")
        try:
            rabbitmq_port = int(os.environ.get("RABBITMQ_PORT", 5672))
        except ValueError:
            logger.warning("Invalid RABBITMQ_PORT value. Defaulting to 5672.")
            rabbitmq_port = 5672
        connection_params = pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port)
        logger.info(f"Connecting using local RabbitMQ at {rabbitmq_host}:{rabbitmq_port}")
    return pika.BlockingConnection(connection_params)

def process_order(order: dict, processed_orders=None):
    """
    Processes the order. For now, just log the order.
    If a list is provided in processed_orders, append the order to it.
    """
    logger.info(f"Processing order: {order.get('order_id')}")
    if processed_orders is not None:
        processed_orders.append(order)

def start_order_consumer(queue_name: str = "orders", processed_orders=None):
    """
    Connects to RabbitMQ, declares the queue (ensuring durability), and starts
    consuming messages. For each received message, it processes the order (and if provided,
    appends it to the processed_orders list) and acknowledges the message.
    """
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        channel.queue_declare(queue=queue_name, durable=True)
    except Exception as e:
        logger.error(f"Error connecting to RabbitMQ: {e}")
        return

    def callback(ch, method, properties, body):
        try:
            order = json.loads(body)
            process_order(order, processed_orders=processed_orders)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(f"Error processing order: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    channel.basic_consume(queue=queue_name, on_message_callback=callback)
    logger.info("Starting consumer. Waiting for messages...")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        logger.info("Consumer interrupted by user. Shutting down...")
        channel.stop_consuming()
    except Exception as e:
        logger.error(f"Unexpected error in consumer: {e}")
    finally:
        connection.close()
        logger.info("RabbitMQ connection closed.")

if __name__ == '__main__':
    start_order_consumer()

__all__ = ["start_order_consumer", "get_rabbitmq_connection"]