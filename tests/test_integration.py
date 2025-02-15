import socket
import time
import threading
import simplefix
import pytest
from ..fix_core import build_order_message, reset_sequence
from ..fix_server import server_thread, handle_client

HOST = "localhost"

# Use a function-scoped fixture to start a fresh server instance for each test.
@pytest.fixture(scope="function")
def start_fix_server():
    reset_sequence()  # Reset global sequence for test isolation.
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
    
    server_thread_instance = threading.Thread(target=server_loop, daemon=True)
    server_thread_instance.start()
    time.sleep(1)
    yield port
    server_socket.close()
    time.sleep(1)

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

def test_order_submission_flow(start_fix_server):
    """
    Test that when a FIX order is submitted, an execution report (MsgType "8") is received.
    """
    port = start_fix_server
    order_id = "TEST_ORDER"
    symbol = "BOND_XYZ"
    quantity = "100"
    price = "101.50"
    
    order_msg = build_order_message(order_id, symbol, quantity, price)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, port))
    client_socket.sendall(order_msg)
    responses = collect_responses(client_socket, timeout=5)
    client_socket.close()
    
    response_str = responses.decode("ascii").replace("\x01", "|")
    assert "35=8" in response_str, "Expected Execution Report (MsgType 8) not found in response."
    assert f"11={order_id}" in response_str, "Order ID not echoed in Execution Report."
    assert f"55={symbol}" in response_str, "Symbol not echoed in Execution Report."

def test_heartbeat_flow(start_fix_server):
    """
    Test that if no order is sent, the server sends a heartbeat (MsgType "0").
    """
    port = start_fix_server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, port))
    # Do not send any order; wait a bit longer than the heartbeat interval.
    time.sleep(HEARTBEAT_INTERVAL + 2)  # Wait (5+2) = 7 seconds.
    responses = collect_responses(client_socket, timeout=5)
    client_socket.close()
    
    response_str = responses.decode("ascii").replace("\x01", "|")
    assert "35=0" in response_str, "Expected Heartbeat (MsgType 0) not received within expected timeframe."

def test_out_of_sequence(start_fix_server):
    """
    Test that when two orders are sent in one connection, their sequence numbers are consecutive.
    """
    port = start_fix_server
    order_id = "TEST_ORDER_SEQ"
    symbol = "BOND_XYZ"
    quantity = "100"
    price = "101.50"
    
    msg1 = build_order_message(order_id, symbol, quantity, price)  # Expected seq: 1
    msg2 = build_order_message(order_id, symbol, quantity, price)  # Expected seq: 2
    
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, port))
    client_socket.sendall(msg1)
    time.sleep(0.5)
    client_socket.sendall(msg2)
    
    responses = collect_responses(client_socket, timeout=5)
    client_socket.close()
    
    responses_str = responses.decode("ascii").replace("\x01", "|")
    # Check that there are at least two execution reports.
    assert responses_str.count("35=8") >= 2, "Expected at least two Execution Reports."
    
    # Extract sequence numbers from responses.
    seq_numbers = []
    for part in responses_str.split("|"):
        if part.startswith("34="):
            try:
                seq_numbers.append(int(part.split("=")[1]))
            except ValueError:
                continue
    assert len(seq_numbers) >= 2, "Not enough sequence numbers found in responses."
    # Check that the last two sequence numbers are consecutive.
    assert seq_numbers[-1] - seq_numbers[-2] == 1, "Sequence numbers are not consecutive."

# Define the heartbeat interval so tests can reference it.
HEARTBEAT_INTERVAL = 10