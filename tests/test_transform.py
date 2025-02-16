import json
import socket
import time
import threading
import requests
import pytest
from fix_core import build_order_message, reset_sequence
from fix_server import handle_client  # Ensure your FIX server now pushes to the API via process_fix_message
from internal_api import app  # Your Flask API code

HOST = "localhost"

# Fixture to start a fresh FIX server on a free port.
@pytest.fixture(scope="function")
def start_fix_server():
    reset_sequence()  # Reset the global sequence for isolation.
    # Create a server socket on a free port.
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

# Fixture to start the internal API server (Flask) on a fixed port (e.g., 5001).
@pytest.fixture(scope="function")
def start_internal_api():
    port = 5001
    # Start the Flask app in a separate thread.
    thread = threading.Thread(
        target=app.run,
        kwargs={'debug': False, 'port': port, 'use_reloader': False}
    )
    thread.setDaemon(True)
    thread.start()
    time.sleep(1)  # Give the API time to start.
    yield port

def collect_responses(client_socket, timeout=5):
    client_socket.settimeout(timeout)
    responses = b""
    try:
        while True:
            part = client_socket.recv(4096)
            if not part:
                break
            responses += part
    except socket.timeout:
        pass
    return responses

def test_full_end_to_end_flow(start_fix_server, start_internal_api):
    """
    Test the complete flow:
      - A FIX order is sent to the FIX server.
      - The server processes and transforms it, then pushes the enriched order
        to the internal API.
      - A GET request to the internal API returns the enriched order.
    """
    api_port = start_internal_api  # Should be 5001.
    API_URL = f"http://{HOST}:{api_port}/orders"
    
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
    
    # Wait a bit for the server to process the order and push it to the API.
    time.sleep(3)
    
    # Query the internal API to retrieve orders.
    try:
        response = requests.get(API_URL)
    except requests.exceptions.ConnectionError as ce:
        pytest.fail(f"Internal API connection failed: {ce}")
    
    data = response.json()
    orders_list = data.get("orders", [])
    matching_orders = [o for o in orders_list if o.get("order_id") == order_id]
    assert len(matching_orders) > 0, "The enriched order was not found in the internal API."