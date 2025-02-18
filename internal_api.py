from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import datetime
import logging
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

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

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

# New endpoint for logs
@app.route('/logs', methods=['GET'])
def get_logs():
    """
    Returns simulated log entries based on ingested orders.
    """
    try:
        # For this prototype, generate one log entry per order.
        logs = [
            f"Order {order.get('order_id')} ingested at {order.get('ingested_timestamp')}"
            for order in orders
        ]
        if not logs:
            logs = ["No orders ingested yet."]
        return jsonify({"status": "success", "logs": logs}), 200
    except Exception as e:
        app.logger.error(f"Error in get_logs: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

# Serve the React app
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react_app(path):
    # If the requested resource exists, serve it. Otherwise, serve index.html.
    file_path = os.path.join(app.static_folder, path)
    if path != "" and os.path.exists(file_path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')
                                   
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5002))
    app.run(host="0.0.0.0", port=port, debug=False)
