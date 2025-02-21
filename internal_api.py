from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import datetime
import logging
import os

# Import the publisher function
from rabbitmq_publisher import publish_order

def create_app(test_config=None):
    # Set up the static folder path
    static_path = os.path.join(os.path.dirname(__file__), "static")
    
    # Create the Flask app instance
    app = Flask(__name__, static_folder=static_path, static_url_path="")
    CORS(app)  # Enable CORS for all routes

    # Configure logging to output to the console.
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger(__name__)

    # In-memory store for orders (for internal UI display)
    orders = []
    # Attach the orders list to the app so it can be accessed in tests
    app.orders = orders

    @app.route('/orders', methods=['POST'])
    def receive_order():
        """
        Receives enriched FIX data in JSON format, stores it in memory, 
        publishes it to RabbitMQ, and returns a success response.
        """
        try:
            data = request.get_json(silent=True)
            if data is None:
                logger.error("Received invalid JSON")
                return jsonify({"status": "error", "message": "Invalid JSON"}), 400

            data.setdefault("ingested_timestamp", datetime.datetime.now(datetime.timezone.utc).isoformat())
            orders.append(data)
            logger.info(f"Order received: {data}")

            try:
                publish_order(data)
                logger.info(f"Order published to RabbitMQ: {data.get('order_id')}")
            except Exception as pub_err:
                logger.error(f"Failed to publish order to RabbitMQ: {pub_err}")
                # You can choose to return an error or continue with a success response

            return jsonify({"status": "success", "message": "Order ingested"}), 200
        except Exception as e:
            logger.error(f"Error in receive_order: {e}")
            return jsonify({"status": "error", "message": "Internal server error"}), 500

    @app.route('/orders', methods=['GET'])
    def list_orders():
        try:
            logger.info("Listing orders")
            return jsonify({"status": "success", "orders": orders}), 200
        except Exception as e:
            logger.error(f"Error in list_orders: {e}")
            return jsonify({"status": "error", "message": "Internal server error"}), 500

    @app.route('/orders/<order_id>', methods=['DELETE'])
    def delete_order(order_id):
        try:
            nonlocal orders
            initial_count = len(orders)
            orders = [order for order in orders if order.get("order_id") != order_id]
            app.orders = orders  # Update the attached orders list
            if len(orders) < initial_count:
                logger.info(f"Order {order_id} deleted")
                return jsonify({"status": "success", "message": f"Order {order_id} deleted"}), 200
            else:
                logger.warning(f"Order {order_id} not found")
                return jsonify({"status": "error", "message": f"Order {order_id} not found"}), 404
        except Exception as e:
            logger.error(f"Error in delete_order: {e}")
            return jsonify({"status": "error", "message": "Internal server error"}), 500

    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({"status": "ok"}), 200

    @app.route('/logs', methods=['GET'])
    def get_logs():
        try:
            logs = [
                f"Order {order.get('order_id')} ingested at {order.get('ingested_timestamp')}"
                for order in orders
            ]
            if not logs:
                logs = ["No orders ingested yet."]
            return jsonify({"status": "success", "logs": logs}), 200
        except Exception as e:
            logger.error(f"Error in get_logs: {e}")
            return jsonify({"status": "error", "message": "Internal server error"}), 500

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_react_app(path):
        file_path = os.path.join(app.static_folder, path)
        logger.info(f"Requested path: {path} | Full file path: {file_path}")
        if path != "" and os.path.exists(file_path):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, 'index.html')

    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get("PORT", 5002))
    app.run(host="0.0.0.0", port=port, debug=False)