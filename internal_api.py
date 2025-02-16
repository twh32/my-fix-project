
from flask import Flask, request, jsonify
import datetime

app = Flask(__name__)

# In-memory store for orders
orders = []

@app.route('/orders', methods=['POST'])
def receive_order():
    """
    Receives enriched FIX data in JSON format, stores it, and returns a success response.
    """
    # Parse JSON data from the request using silent=True.
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"status": "error", "message": "Invalid JSON"}), 400
    
    # Add a received timestamp if not already present.
    data.setdefault("ingested_timestamp", datetime.datetime.now(datetime.timezone.utc).isoformat())
    
    orders.append(data)
    return jsonify({"status": "success", "message": "Order ingested"}), 200

@app.route('/orders', methods=['GET'])
def list_orders():
    """
    Returns the list of all ingested orders.
    """
    return jsonify({"status": "success", "orders": orders}), 200

@app.route('/orders/<order_id>', methods=['DELETE'])
def delete_order(order_id):
    """
    Deletes an order with the given order_id.
    """
    global orders
    initial_count = len(orders)
    orders = [order for order in orders if order.get("order_id") != order_id]
    if len(orders) < initial_count:
        return jsonify({"status": "success", "message": f"Order {order_id} deleted"}), 200
    else:
        return jsonify({"status": "error", "message": f"Order {order_id} not found"}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5001)