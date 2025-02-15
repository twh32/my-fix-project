import socket
import simplefix
import time
import select
import threading
import logging

# Set up basic logging configuration.
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def build_execution_report(order_msg):
    """
    Build an Execution Report FIX message in response to an order message.
    This function extracts key fields (e.g. ClOrdID, MsgSeqNum) from the order
    and constructs a new FIX message that simulates an execution report.
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
    exec_msg.append_pair(8, "FIX.4.2")           # BeginString
    exec_msg.append_pair(35, "8")                # MsgType: Execution Report
    exec_msg.append_pair(11, cl_ord_id if cl_ord_id else "UNKNOWN")
    if msg_seq_num is not None:
        exec_msg.append_pair(34, str(msg_seq_num))  # Echo the sequence number
    exec_msg.append_pair(17, "EXEC456")          # ExecID
    exec_msg.append_pair(39, "2")                # OrdStatus: Filled
    exec_msg.append_pair(150, "F")               # ExecType: Fill
    # Copy order details: Symbol (55), OrderQty (38), Price (44)
    for tag in [55, 38, 44]:
        for t, v in order_msg:
            if t == tag:
                exec_msg.append_pair(tag, v)
                break
    return exec_msg.encode()

def send_heartbeat(conn):
    """
    Build and send a Heartbeat FIX message.
    """
    hb_msg = simplefix.FixMessage()
    hb_msg.append_pair(8, "FIX.4.2")
    hb_msg.append_pair(35, "0")               # Heartbeat message type
    hb_msg.append_utc_timestamp(52)           # SendingTime
    conn.sendall(hb_msg.encode())
    logging.info("Sent Heartbeat.")

def handle_client(conn, addr):
    """
    Handle communication with a connected client.
    Each client gets its own expected sequence number.
    """
    logging.info(f"Connected by {addr}")
    parser = simplefix.FixParser()
    # Maintain a per-client expected sequence number.
    expected_seq_num = 1
    last_activity = time.time()
    try:
        while True:
            # Wait for data with a timeout for heartbeat.
            rlist, _, _ = select.select([conn], [], [], 5)
            if rlist:
                data = conn.recv(4096)
                if not data:
                    logging.info(f"Client {addr} disconnected.")
                    break
                last_activity = time.time()
                parser.append_buffer(data)
                while True:
                    order_msg = parser.get_message()
                    if order_msg is None:
                        break
                    logging.info("Received Order FIX message:")
                    for tag, value in order_msg:
                        logging.info(f"  Tag {tag}: {value}")
                    # Validate sequence number.
                    received_seq_num = None
                    for tag, value in order_msg:
                        if tag == 34:
                            try:
                                received_seq_num = int(value)
                            except ValueError:
                                received_seq_num = None
                            break
                    if received_seq_num is not None:
                        if received_seq_num != expected_seq_num:
                            logging.warning(f"Expected sequence number {expected_seq_num} but received {received_seq_num}")
                        else:
                            logging.info("Sequence number is as expected.")
                    else:
                        logging.warning("No sequence number (tag 34) found in the message.")
                    
                    # Build and send the execution report.
                    response = build_execution_report(order_msg)
                    conn.sendall(response)
                    logging.info("Sent Execution Report.")
                    expected_seq_num += 1
            else:
                # No data received within the heartbeat interval; send a heartbeat.
                if time.time() - last_activity >= 5:
                    send_heartbeat(conn)
                    last_activity = time.time()
    except Exception as e:
        logging.error(f"An error occurred with client {addr}: {e}")
    finally:
        conn.close()
        logging.info(f"Connection with {addr} closed.")

def run_server(host='localhost', port=5001):
    """
    Main server loop that accepts new client connections.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)  # Allow multiple pending connections.
    logging.info(f"Server listening on {host}:{port}")
    
    try:
        while True:
            conn, addr = server_socket.accept()
            # Handle each client in a new thread.
            client_thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            client_thread.start()
            logging.info("Waiting for new connections...\n")
    except KeyboardInterrupt:
        logging.info("Server shutting down.")
    finally:
        server_socket.close()

if __name__ == '__main__':
    run_server()
