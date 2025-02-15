import socket
import simplefix
import threading
import select
import time

HEARTBEAT_INTERVAL = 5  # seconds

def build_execution_report(order_msg):
    # (Same as before)
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
    conn.sendall(hb_msg.encode())
    print("Sent Heartbeat.")

def handle_client(conn, addr):
    print(f"Connected by {addr}")
    parser = simplefix.FixParser()
    try:
        while True:
            # Wait for data with timeout equal to HEARTBEAT_INTERVAL.
            rlist, _, _ = select.select([conn], [], [], HEARTBEAT_INTERVAL)
            if rlist:
                data = conn.recv(4096)
                if not data:
                    print(f"Client {addr} disconnected.")
                    break
                parser.append_buffer(data)
                while True:
                    msg = parser.get_message()
                    if msg is None:
                        break
                    print("Received FIX message:")
                    for tag, value in msg:
                        print(f"  Tag {tag}: {value}")
                    # Send execution report for each received FIX order.
                    response = build_execution_report(msg)
                    conn.sendall(response)
            else:
                # Timeout reached; send heartbeat.
                try:
                    send_heartbeat(conn)
                    print(f"Heartbeat sent to {addr}")
                except Exception as e:
                    print(f"Error sending heartbeat to {addr}: {e}")
                    break
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
    server_thread()