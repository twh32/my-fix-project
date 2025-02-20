import socket
import simplefix
import threading
import select
import time
import logging

from fix_core import build_order_message  # For building orders if needed
from fix_transform import transform_fix_to_json  # Transformation logic
from rabbitmq_publisher import publish_order  # RabbitMQ publishing function

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Set heartbeat interval (seconds)
HEARTBEAT_INTERVAL = 5

def build_execution_report(order_msg):
    """
    Build an Execution Report FIX message in response to an order message.
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
    exec_msg.append_pair(35, "8")  # Execution Report
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
    """
    Sends a heartbeat message to the connected FIX client.
    """
    hb_msg = simplefix.FixMessage()
    hb_msg.append_pair(8, "FIX.4.2")
    hb_msg.append_pair(35, "0")  # Heartbeat message
    hb_msg.append_utc_timestamp(52)
    try:
        conn.sendall(hb_msg.encode())
        logger.info("Sent Heartbeat.")
    except Exception as e:
        logger.error(f"Error sending heartbeat: {e}")

def process_order_and_publish(msg):
    """
    Transforms the FIX message into enriched data and publishes it to RabbitMQ.
    """
    enriched_data = transform_fix_to_json(msg)
    try:
        publish_order(enriched_data)
        logger.info(f"Enriched order published to RabbitMQ: {enriched_data.get('order_id')}")
    except Exception as e:
        logger.error(f"Exception while publishing order to RabbitMQ: {e}")

def handle_client(conn, addr):
    logger.info(f"Connected by {addr}")
    parser = simplefix.FixParser()
    last_activity = time.time()
    try:
        while True:
            # Wait for data with a timeout equal to HEARTBEAT_INTERVAL.
            rlist, _, _ = select.select([conn], [], [], HEARTBEAT_INTERVAL)
            if rlist:
                data = conn.recv(4096)
                if not data:
                    logger.info(f"Client {addr} disconnected.")
                    break
                last_activity = time.time()
                parser.append_buffer(data)
                while True:
                    msg = parser.get_message()
                    if msg is None:
                        break
                    logger.info("Received FIX message:")
                    for tag, value in msg:
                        logger.info(f"  Tag {tag}: {value}")
                    # Send execution report back to the client.
                    response = build_execution_report(msg)
                    try:
                        conn.sendall(response)
                    except Exception as e:
                        logger.error(f"Error sending execution report: {e}")
                    # Process the FIX message and publish the enriched order to RabbitMQ.
                    process_order_and_publish(msg)
            else:
                # Timeout reached; send heartbeat.
                send_heartbeat(conn)
                last_activity = time.time()
    except Exception as e:
        logger.error(f"Error in handle_client for {addr}: {e}")
    finally:
        conn.close()

def server_thread(host='localhost', port=6000):
    """
    Main server thread that accepts client connections.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(5)
    logger.info(f"Server listening on {host}:{port}")
    try:
        while True:
            conn, addr = server_socket.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        server_socket.close()

if __name__ == '__main__':
    server_thread(host='localhost', port=6000)