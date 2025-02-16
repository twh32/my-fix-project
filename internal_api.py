from flask import Flask, request, jsonify
import datetime
import logging

app = Flask(__name__)

# Configure logging to output to the console.
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# In-memory store for orders
orders = []

@app.route('/orders', methods=['POST'])
def receive_order():
    """
    Receives enriched FIX data in JSON format, stores it, and returns a success response.
    """
    try:
        # Parse JSON data from the request using silent=True.
        data = request.get_json(silent=True)
        if data is None:
            app.logger.error("Received invalid JSON")
            return jsonify({"status": "error", "message": "Invalid JSON"}), 400
        
        # Add a received timestamp if not already present.
        data.setdefault("ingested_timestamp", datetime.datetime.now(datetime.timezone.utc).isoformat())
        
        orders.append(data)
        app.logger.info(f"Order received: {data}")
        return jsonify({"status": "success", "message": "Order ingested"}), 200
    except Exception as e:
        app.logger.error(f"Error in receive_order: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@app.route('/orders', methods=['GET'])
def list_orders():
    """
    Returns the list of all ingested orders.
    """
    try:
        app.logger.info("Listing orders")
        return jsonify({"status": "success", "orders": orders}), 200
    except Exception as e:
        app.logger.error(f"Error in list_orders: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@app.route('/orders/<order_id>', methods=['DELETE'])
def delete_order(order_id):
    """
    Deletes an order with the given order_id.
    """
    try:
        global orders
        initial_count = len(orders)
        orders = [order for order in orders if order.get("order_id") != order_id]
        if len(orders) < initial_count:
            app.logger.info(f"Order {order_id} deleted")
            return jsonify({"status": "success", "message": f"Order {order_id} deleted"}), 200
        else:
            app.logger.warning(f"Order {order_id} not found")
            return jsonify({"status": "error", "message": f"Order {order_id} not found"}), 404
    except Exception as e:
        app.logger.error(f"Error in delete_order: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

if __name__ == '__main__':
    # Run the app on all interfaces on port 5002 with debug mode off.
    app.run(host="0.0.0.0", port=5002, debug=False)