import tkinter as tk
from tkinter import ttk
import requests
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# URL for the internal API endpoint that provides the list of orders.
API_URL = "http://localhost:5001/orders"  # Adjust if your API is running on a different port

class OrderViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Internal Order Viewer")
        self.geometry("800x400")

        # Create a Treeview widget for displaying orders
        self.tree = ttk.Treeview(self)
        self.tree["columns"] = ("order_id", "symbol", "quantity", "price", "ingested_timestamp")
        self.tree.heading("#0", text="Index")
        self.tree.heading("order_id", text="Order ID")
        self.tree.heading("symbol", text="Symbol")
        self.tree.heading("quantity", text="Quantity")
        self.tree.heading("price", text="Price")
        self.tree.heading("ingested_timestamp", text="Ingested Timestamp")
        
        self.tree.column("#0", width=50)
        self.tree.column("order_id", width=100)
        self.tree.column("symbol", width=100)
        self.tree.column("quantity", width=100)
        self.tree.column("price", width=100)
        self.tree.column("ingested_timestamp", width=200)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Refresh button to manually trigger data update
        refresh_btn = ttk.Button(self, text="Refresh Orders", command=self.refresh_orders)
        refresh_btn.pack(pady=(0,5))

        # Status label for monitoring messages
        self.status_label = ttk.Label(self, text="Status: Ready")
        self.status_label.pack(pady=(0,10))

        # Start periodic refresh every 10 seconds
        self.after(10000, self.refresh_orders)

    def refresh_orders(self):
        """Fetch orders from the internal API and update the UI."""
        logging.info("Refreshing orders from API...")
        try:
            response = requests.get(API_URL)
            if response.status_code == 200:
                data = response.json()
                orders = data.get("orders", [])
                # Clear existing entries in the Treeview
                for item in self.tree.get_children():
                    self.tree.delete(item)
                # Insert each order into the Treeview
                for idx, order in enumerate(orders, start=1):
                    self.tree.insert("", "end", text=str(idx),
                                     values=(order.get("order_id", ""),
                                             order.get("symbol", ""),
                                             order.get("quantity", ""),
                                             order.get("price", ""),
                                             order.get("ingested_timestamp", "")))
                self.status_label.config(text=f"Status: {len(orders)} orders loaded")
                logging.info(f"Loaded {len(orders)} orders")
            else:
                err_msg = f"Error fetching orders (Status code: {response.status_code})"
                self.status_label.config(text=f"Status: {err_msg}")
                logging.error(err_msg)
        except Exception as e:
            err_msg = f"Exception during fetching orders: {e}"
            self.status_label.config(text="Status: Error fetching orders")
            logging.error(err_msg)
        # Schedule the next refresh in 10 seconds
        self.after(10000, self.refresh_orders)

if __name__ == '__main__':
    app = OrderViewer()
    app.mainloop()