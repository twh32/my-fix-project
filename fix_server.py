import socket
import simplefix
import threading
import select
import time
import requests

from fix_core import build_order_message  # For building orders (if needed)
from fix_transform import transform_fix_to_json  # Transformation logic

# Set heartbeat interval (seconds)
HEARTBEAT_INTERVAL = 5
# URL of the internal API (adjust the port if necessary)
INTERNAL_API_URL = "http://localhost:5001/orders"

def build_execution_report(order_msg):
    """
    Build an Execution Report FIX message in response to an order message.
    (This remains unchanged from before.)
    """
    cl_ord_id = None
    msg_seq_num = None
    for tag, value in order_msg:
        if tag == 11:
            cl_ord_id = value
        if tag == 34:
            try:
                msg_seq_num = int(value)
            except ValueError:
                msg_seq_num = 0
    exec_msg = simplefix.FixMessage()
    exec_msg.append_pair(8, "FIX.4.2")
    exec_msg.append_pair(35, "8")
    exec_msg.append_pair(11, cl_ord_id if cl_ord_id else "UNKNOWN")
    if msg_seq_num is not None:
        exec_msg.append_pair(34, str(msg_seq_num))
    exec_msg.append_pair(17, "EXEC456")
    exec_msg.append_pair(39, "2")
    exec_msg.append_pair(150, "F")
    for tag in [55, 38, 44]:
        for t, v in order_msg:
            if t == tag:
                exec_msg.append_pair(tag, v)
                break
    return exec_msg.encode()

def send_heartbeat(conn):
    hb_msg = simplefix.FixMessage()
    hb_msg.append_pair(8, "FIX.4.2")
    hb_msg.append_pair(35, "0")
    hb_msg.append_utc_timestamp(52)
    try:
        conn.sendall(hb_msg.encode())
        print("Sent Heartbeat.")
    except Exception as e:
        print("Error sending heartbeat:", e)

def process_and_push_order(msg):
    """
    Transforms the FIX message into enriched data and pushes it to the internal API.
    """
    enriched_data = transform_fix_to_json(msg)
    try:
        response = requests.post(INTERNAL_API_URL, json=enriched_data)
        if response.status_code == 200:
            print("Enriched order pushed to API successfully.")
        else:
            print(f"Failed to push order to API. Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print("Exception while pushing order to API:", e)

def handle_client(conn, addr):
    print(f"Connected by {addr}")
    parser = simplefix.FixParser()
    last_activity = time.time()
    try:
        while True:
            # Wait for data with a timeout equal to HEARTBEAT_INTERVAL.
            rlist, _, _ = select.select([conn], [], [], HEARTBEAT_INTERVAL)
            if rlist:
                data = conn.recv(4096)
                if not data:
                    print(f"Client {addr} disconnected.")
                    break
                last_activity = time.time()
                parser.append_buffer(data)
                while True:
                    msg = parser.get_message()
                    if msg is None:
                        break
                    print("Received FIX message:")
                    for tag, value in msg:
                        print(f"  Tag {tag}: {value}")
                    # Send execution report for the FIX order.
                    response = build_execution_report(msg)
                    try:
                        conn.sendall(response)
                    except Exception as e:
                        print("Error sending execution report:", e)
                    # Process the FIX message and push it to the internal API.
                    process_and_push_order(msg)
            else:
                # Timeout reached; send heartbeat.
                send_heartbeat(conn)
                last_activity = time.time()
    except Exception as e:
        print(f"Error in handle_client for {addr}: {e}")
    finally:
        conn.close()

def server_thread(host='localhost', port=5001):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Server listening on {host}:{port}")
    try:
        while True:
            conn, addr = server_socket.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except Exception as e:
        print("Server error:", e)
    finally:
        server_socket.close()

if __name__ == '__main__':
    server_thread(host='localhost', port=6000)