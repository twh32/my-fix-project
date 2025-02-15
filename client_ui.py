import tkinter as tk
from tkinter import ttk
import socket
import simplefix
import time
from fix_core import build_order_message

# Global sequence number for outgoing messages
sequence_number = 1

def submit_order():
    """Reads form data, builds the FIX order message, sends it, and displays the response."""
    order_id = entry_order_id.get()
    symbol = entry_symbol.get()
    quantity = entry_quantity.get()
    price = entry_price.get()

    # Connection details – adjust if necessary.
    host = "localhost"
    port = 5001

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
    except Exception as e:
        text_output.insert(tk.END, f"Error connecting to server: {e}\n")
        return

    # Build the FIX order message.
    order_msg = build_order_message(order_id, symbol, quantity, price)
    # For display, replace the SOH delimiter ("\x01") with a pipe ("|").
    readable_order = order_msg.decode("ascii").replace("\x01", "|")
    text_output.insert(tk.END, f"Sending Order FIX message:\n{readable_order}\n")

    # Send the order message.
    client_socket.sendall(order_msg)

    # Set a timeout for receiving data.
    client_socket.settimeout(15)
    text_output.insert(tk.END, "\nWaiting for further messages (e.g., heartbeats)...\n")
    
    try:
        while True:
            response = client_socket.recv(4096)
            if not response:
                text_output.insert(tk.END, "Server closed the connection.\n")
                break
            readable_response = response.decode("ascii").replace("\x01", "|")
            text_output.insert(tk.END, f"\nReceived message:\n{readable_response}\n")
    except socket.timeout:
        text_output.insert(tk.END, "\nNo more messages received (timeout reached).\n")
    except Exception as e:
        text_output.insert(tk.END, f"\nError receiving message: {e}\n")
    finally:
        client_socket.close()

# ---------------------------
# Build the Tkinter GUI
# ---------------------------
root = tk.Tk()
root.title("FIX Order Submission Client")

# Frame for input fields.
frame_inputs = ttk.Frame(root, padding="10")
frame_inputs.grid(row=0, column=0, sticky="EW")

# Order ID
ttk.Label(frame_inputs, text="Order ID:").grid(row=0, column=0, sticky="W")
entry_order_id = ttk.Entry(frame_inputs)
entry_order_id.grid(row=0, column=1, sticky="EW")
entry_order_id.insert(0, "ORDER123")  # Default value

# Symbol
ttk.Label(frame_inputs, text="Symbol:").grid(row=1, column=0, sticky="W")
entry_symbol = ttk.Entry(frame_inputs)
entry_symbol.grid(row=1, column=1, sticky="EW")
entry_symbol.insert(0, "BOND_XYZ")

# Quantity
ttk.Label(frame_inputs, text="Quantity:").grid(row=2, column=0, sticky="W")
entry_quantity = ttk.Entry(frame_inputs)
entry_quantity.grid(row=2, column=1, sticky="EW")
entry_quantity.insert(0, "100")

# Price
ttk.Label(frame_inputs, text="Price:").grid(row=3, column=0, sticky="W")
entry_price = ttk.Entry(frame_inputs)
entry_price.grid(row=3, column=1, sticky="EW")
entry_price.insert(0, "101.50")

frame_inputs.columnconfigure(1, weight=1)

# Submit Order Button
btn_submit = ttk.Button(root, text="Submit Order", command=submit_order)
btn_submit.grid(row=1, column=0, padx=10, pady=5, sticky="EW")

# Text widget to display responses and logs.
text_output = tk.Text(root, height=15, wrap="word")
text_output.grid(row=2, column=0, padx=10, pady=10, sticky="NSEW")

# Add a vertical scrollbar to the text widget.
scrollbar = ttk.Scrollbar(root, orient="vertical", command=text_output.yview)
text_output.configure(yscrollcommand=scrollbar.set)
scrollbar.grid(row=2, column=1, sticky="NS")

# Allow the text widget to expand.
root.columnconfigure(0, weight=1)
root.rowconfigure(2, weight=1)

# Start the Tkinter event loop.
root.mainloop()