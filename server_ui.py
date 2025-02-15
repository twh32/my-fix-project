import socket
import simplefix
import time
import select
import threading
import queue
import tkinter as tk
from tkinter import ttk

# Thread-safe queue for log messages
log_queue = queue.Queue()

# Global heartbeat interval (seconds)
HEARTBEAT_INTERVAL = 5

# Global dictionary to maintain expected sequence numbers per client (keyed by SenderCompID)
session_seq_numbers = {}

def build_execution_report(order_msg):
    """
    Build an Execution Report FIX message in response to an order message.
    Extract key fields (e.g., ClOrdID, MsgSeqNum) and construct a FIX message.
    """
    cl_ord_id = None
    msg_seq_num = None
    sender = None
    for tag, value in order_msg:
        if tag == 11:
            cl_ord_id = value
        if tag == 34:
            try:
                msg_seq_num = int(value)
            except ValueError:
                msg_seq_num = 0
        if tag == 49:
            sender = value.decode() if isinstance(value, bytes) else value
    exec_msg = simplefix.FixMessage()
    exec_msg.append_pair(8, "FIX.4.2")           # BeginString
    exec_msg.append_pair(35, "8")                # MsgType: Execution Report
    exec_msg.append_pair(11, cl_ord_id if cl_ord_id else "UNKNOWN")
    if msg_seq_num is not None:
        exec_msg.append_pair(34, str(msg_seq_num))  # Echo the sequence number
    exec_msg.append_pair(17, "EXEC456")          # ExecID
    exec_msg.append_pair(39, "2")                # OrdStatus: Filled
    exec_msg.append_pair(150, "F")               # ExecType: Fill
    # Optionally, copy order details: Symbol (55), OrderQty (38), Price (44)
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
    hb_msg.append_pair(35, "0")  # Heartbeat message
    hb_msg.append_utc_timestamp(52)
    conn.sendall(hb_msg.encode())
    log_queue.put("Sent Heartbeat.")

def handle_client(conn, addr):
    """
    Handle communication with a connected client.
    This function runs in its own thread.
    """
    log_queue.put(f"Connected by {addr}")
    parser = simplefix.FixParser()
    last_activity = time.time()
    # We'll use the SenderCompID (tag 49) as a key to maintain session sequence numbers.
    client_id = None

    try:
        while True:
            # Wait for data with timeout for heartbeat.
            rlist, _, _ = select.select([conn], [], [], HEARTBEAT_INTERVAL)
            if rlist:
                data = conn.recv(4096)
                if not data:
                    log_queue.put(f"Client {addr} disconnected.")
                    break
                last_activity = time.time()
                parser.append_buffer(data)
                while True:
                    order_msg = parser.get_message()
                    if order_msg is None:
                        break

                    log_queue.put("Received Order FIX message:")
                    for tag, value in order_msg:
                        log_queue.put(f"  Tag {tag}: {value}")

                    # Extract SenderCompID (tag 49) to use as client ID
                    for tag, value in order_msg:
                        if tag == 49:
                            client_id = value.decode() if isinstance(value, bytes) else value
                            break
                    if client_id is None:
                        client_id = "UNKNOWN"

                    # Get the expected sequence number from our global session dictionary.
                    expected_seq_num = session_seq_numbers.get(client_id, 1)

                    # Validate sequence number
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
                            log_queue.put(f"Warning for {client_id}: Expected sequence number {expected_seq_num} but received {received_seq_num}")
                        else:
                            log_queue.put(f"Sequence number for {client_id} is as expected.")
                    else:
                        log_queue.put("No sequence number (tag 34) found in the message.")

                    # Build and send execution report.
                    response = build_execution_report(order_msg)
                    conn.sendall(response)
                    log_queue.put("Sent Execution Report.")

                    # Update the expected sequence number and store it.
                    expected_seq_num = (received_seq_num + 1) if received_seq_num is not None else expected_seq_num + 1
                    session_seq_numbers[client_id] = expected_seq_num

            else:
                # Timeout reached; no data received—send heartbeat.
                if time.time() - last_activity >= HEARTBEAT_INTERVAL:
                    send_heartbeat(conn)
                    last_activity = time.time()
    except Exception as e:
        log_queue.put(f"An error occurred with client {addr}: {e}")
    finally:
        conn.close()
        log_queue.put(f"Connection with {addr} closed.")

def server_thread(host='localhost', port=5001):
    """
    The main server thread that accepts new client connections.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    log_queue.put(f"Server listening on {host}:{port}")
    try:
        while True:
            conn, addr = server_socket.accept()
            client_handler = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            client_handler.start()
            log_queue.put("Waiting for new connections...")
    except Exception as e:
        log_queue.put(f"Server error: {e}")
    finally:
        server_socket.close()

def start_server():
    """
    Start the server in a background thread.
    """
    t = threading.Thread(target=server_thread, daemon=True)
    t.start()

def poll_queue(text_widget):
    """
    Periodically poll the log_queue and update the text_widget.
    """
    try:
        while True:
            message = log_queue.get_nowait()
            text_widget.insert(tk.END, message + "\n")
            text_widget.see(tk.END)
    except queue.Empty:
        pass
    text_widget.after(100, poll_queue, text_widget)

# ---------------------------
# Build the Tkinter Dashboard UI
# ---------------------------
root = tk.Tk()
root.title("FIX Server Dashboard")

# Create a frame for the log display.
frame_log = ttk.Frame(root, padding="10")
frame_log.grid(row=0, column=0, sticky="NSEW")

# Text widget for logging.
text_log = tk.Text(frame_log, height=20, wrap="word")
text_log.grid(row=0, column=0, sticky="NSEW")

# Add a vertical scrollbar.
scrollbar = ttk.Scrollbar(frame_log, orient="vertical", command=text_log.yview)
text_log.configure(yscrollcommand=scrollbar.set)
scrollbar.grid(row=0, column=1, sticky="NS")

# Configure grid weights.
frame_log.columnconfigure(0, weight=1)
frame_log.rowconfigure(0, weight=1)
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

# Start the server thread.
start_server()

# Start polling the log queue to update the UI.
poll_queue(text_log)

# Start the Tkinter main loop.
root.mainloop()