import json
import socket
import time
import threading
import pytest
import pika

from fix_core import build_order_message, reset_sequence
from fix_server import handle_client
from internal_api import app
from rabbitmq_publisher import get_rabbitmq_connection  # For connecting to RabbitMQ

HOST = "localhost"
QUEUE_NAME = "orders"

# Fixture to start the FIX server on a free port.
@pytest.fixture(scope="function")
def start_fix_server():
    reset_sequence()  # Reset global sequence for isolation.
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, 0))
    port = server_socket.getsockname()[1]
    server_socket.listen(5)
    
    def server_loop():
        try:
            while True:
                conn, addr = server_socket.accept()
                threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
        except Exception as e:
            print("Server loop terminated:", e)
    
    thread = threading.Thread(target=server_loop, daemon=True)
    thread.start()
    time.sleep(1)  # Give the server time to start.
    yield port
    server_socket.close()
    time.sleep(1)

# Fixture to start the internal API on port 5002 (for completeness; not used in this test).
@pytest.fixture(scope="function")
def start_internal_api():
    port = 5002
    thread = threading.Thread(
        target=app.run,
        kwargs={'host': '0.0.0.0', 'port': port, 'debug': False, 'use_reloader': False}
    )
    thread.setDaemon(True)
    thread.start()
    time.sleep(1)  # Give the API time to start.
    yield port

def purge_queue(channel, queue_name):
    channel.queue_purge(queue=queue_name)

def get_order_from_queue(queue_name):
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    # Ensure the queue exists.
    channel.queue_declare(queue=queue_name, durable=True)
    # Retrieve a message without auto-ack (we'll ack manually).
    method_frame, header_frame, body = channel.basic_get(queue=queue_name, auto_ack=True)
    connection.close()
    return method_frame, body

def test_full_end_to_end_flow(start_fix_server, start_internal_api):
    """
    Test the complete flow:
      - A FIX order is sent to the FIX server.
      - The server processes and transforms it, then publishes the enriched order
        to RabbitMQ.
      - Verify that the enriched order appears in the RabbitMQ queue.
    """
    # Purge the "orders" queue to start fresh.
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    purge_queue(channel, QUEUE_NAME)
    connection.close()

    order_id = "ORDER_E2E"
    symbol = "TEST_SYMBOL"
    quantity = "100"
    price = "99.99"

    # Build the FIX order message.
    order_msg = build_order_message(order_id, symbol, quantity, price)

    # Send the FIX order to the FIX server.
    fix_server_port = start_fix_server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, fix_server_port))
    client_socket.sendall(order_msg)
    client_socket.close()

    # Wait for the server to process the order and publish it.
    time.sleep(3)

    # Connect to RabbitMQ and retrieve a message from the "orders" queue.
    method_frame, body = get_order_from_queue(QUEUE_NAME)
    assert method_frame is not None, "No message found in RabbitMQ queue"
    order_data = json.loads(body)
    assert order_data.get("order_id") == order_id, "The enriched order ID does not match"