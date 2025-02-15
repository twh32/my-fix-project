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
    # Parse JSON data from the request
    data = request.get_json()
    if data is None:
        return jsonify({"status": "error", "message": "Invalid JSON"}), 400
    
    # Optionally, add a received timestamp if not already present
    data.setdefault("ingested_timestamp", datetime.datetime.now(datetime.timezone.utc).isoformat())
    
    # "Store" the order in our in-memory list
    orders.append(data)
    
    return jsonify({"status": "success", "message": "Order ingested"}), 200

@app.route('/orders', methods=['GET'])
def list_orders():
    """
    Returns the list of all ingested orders.
    """
    return jsonify({"status": "success", "orders": orders}), 200

if __name__ == '__main__':
    app.run(debug=True)