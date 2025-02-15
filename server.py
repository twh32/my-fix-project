import socket
import simplefix

def run_server(host='localhost', port=5001):
    # Create a TCP socket.
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)
    print(f"Server listening on {host}:{port}")

    # Accept an incoming connection.
    conn, addr = server_socket.accept()
    print(f"Connected by {addr}")

    # Initialize a FIX parser.
    parser = simplefix.FixParser()

    try:
        while True:
            # Receive data in chunks.
            data = conn.recv(4096)
            if not data:
                break  # No more data; client closed connection.
            # Feed the received data into the parser.
            parser.append_buffer(data)
            # Retrieve all complete FIX messages.
            while True:
                msg = parser.get_message()
                if msg is None:
                    break  # No complete message available yet.
                print("Received FIX message:")
                # Iterate directly over the message, which yields (tag, value) pairs.
                for tag, value in msg:
                    print(f"  Tag {tag}: {value}")
    except Exception as e:
        print("An error occurred:", e)
    finally:
        conn.close()
        server_socket.close()

if __name__ == '__main__':
    run_server()
