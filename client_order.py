import socket
import simplefix
import time

# Global sequence number for outgoing messages
sequence_number = 1

def build_order_message():
    global sequence_number
    msg = simplefix.FixMessage()
    msg.append_pair(8, "FIX.4.2")            # BeginString
    msg.append_pair(35, "D")                 # MsgType: New Order Single
    msg.append_pair(11, "ORDER123")          # ClOrdID
    msg.append_pair(34, str(sequence_number))# MsgSeqNum (tag 34)
    msg.append_pair(49, "SENDER")            # SenderCompID
    msg.append_pair(56, "TARGET")            # TargetCompID
    msg.append_utc_timestamp(52)             # SendingTime
    msg.append_pair(55, "BOND_XYZ")          # Symbol
    msg.append_pair(38, "100")               # Order Quantity
    msg.append_pair(44, "101.50")            # Price
    msg.append_pair(98, "0")                 # EncryptMethod
    msg.append_pair(108, "30")               # HeartBtInt
    sequence_number += 1  # Increment for next message
    return msg.encode()

def run_client(host='localhost', port=5001):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    
    # Build and send the order message.
    order_encoded = build_order_message()
    order_readable = order_encoded.decode("ascii").replace("\x01", "|")
    print("Sending Order FIX message:")
    print(order_readable)
    client_socket.sendall(order_encoded)
    
    # Instead of closing immediately, keep the connection open
    # and listen for further messages (like heartbeats).
    print("\nWaiting for further messages (e.g., heartbeats, additional responses)...")
    
    # Set a timeout so recv() doesn't block forever.
    client_socket.settimeout(15)  # Timeout after 15 seconds of inactivity
    try:
        while True:
            response = client_socket.recv(4096)
            if not response:
                # If recv returns an empty bytes object, the connection is closed.
                break
            response_readable = response.decode("ascii").replace("\x01", "|")
            print("\nReceived message:")
            print(response_readable)
    except socket.timeout:
        print("No more messages received (timeout reached).")
    finally:
        client_socket.close()

if __name__ == '__main__':
    run_client()
