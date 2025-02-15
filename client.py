import socket
import simplefix
import time

def run_client(host='localhost', port=5001):
    # Create a TCP socket and connect to the server.
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    # Build a FIX message (a simple Logon message in this example).
    msg = simplefix.FixMessage()
    msg.append_pair(8, "FIX.4.2")         # BeginString
    msg.append_pair(35, "A")              # MsgType: Logon
    msg.append_pair(49, "SENDER")         # SenderCompID
    msg.append_pair(56, "TARGET")         # TargetCompID
    msg.append_utc_timestamp(52)          # SendingTime
    msg.append_pair(98, "0")              # EncryptMethod (0 = None)
    msg.append_pair(108, "30")            # HeartBtInt

    # Encode the message.
    encoded = msg.encode()

    # For display purposes, replace the SOH delimiter ("\x01") with a pipe.
    readable = encoded.decode("ascii").replace("\x01", "|")
    print("Sending FIX message:")
    print(readable)

    # Send the encoded message.
    client_socket.sendall(encoded)
    # Pause to ensure the message is processed.
    time.sleep(1)
    client_socket.close()

if __name__ == '__main__':
    run_client()
