from flask import Flask, request, jsonify
import datetime

app = Flask(__name__)

# In-memory store for orders.
orders = []

@app.route('/orders', methods=['POST'])
def receive_order():
    """
    Receives enriched FIX data in JSON format, stores it, and returns a success response.
    If the request does not contain valid JSON, returns a JSON error.
    """
    # Parse JSON data from the request using silent=True.
    # This prevents Flask from returning its default HTML error page on invalid JSON.
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"status": "error", "message": "Invalid JSON"}), 400

    # Optionally, add a received timestamp if not already present.
    data.setdefault("ingested_timestamp", datetime.datetime.now(datetime.timezone.utc).isoformat())

    # Store the order in the in-memory list.
    orders.append(data)

    return jsonify({"status": "success", "message": "Order ingested"}), 200

@app.route('/orders', methods=['GET'])
def list_orders():
    """
    Returns the list of all ingested orders.
    """
    return jsonify({"status": "success", "orders": orders}), 200

if __name__ == '__main__':
    # Run the Flask app in debug mode (remove debug=True in production).
    app.run(debug=True)