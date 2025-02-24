from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import datetime
import logging
import os

# Import the publisher function
from rabbitmq_publisher import publish_order

# Initialize the database
db = SQLAlchemy()

# Define the Order model
class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String, unique=True, nullable=False)
    ingested_timestamp = db.Column(db.DateTime, nullable=False)
    # Additional order details stored as JSON
    additional_data = db.Column(db.JSON)

    def to_dict(self):
        # Base fields
        data = {
            "order_id": self.order_id,
            "ingested_timestamp": self.ingested_timestamp.isoformat()
        }
        # Merge additional_data if available
        if self.additional_data:
            data.update(self.additional_data)
        return data

def create_app(test_config=None):
    # Set up the static folder path for serving the React app
    static_path = os.path.join(os.path.dirname(__file__), "static")
    app = Flask(__name__, static_folder=static_path, static_url_path="")
    CORS(app)  # Enable CORS for all routes

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)

    # Database configuration: use DATABASE_URL if provided (e.g., on Heroku),
    # otherwise fall back to a local database.
    uri = os.environ.get('DATABASE_URL', 'postgresql://localhost/my_test_db')
    # Heroku returns a URI that starts with "postgres://"; SQLAlchemy expects "postgresql://"
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize SQLAlchemy and Flask-Migrate
    db.init_app(app)
    Migrate(app, db)

    @app.route('/orders', methods=['POST'])
    def receive_order():
        """
        Receives enriched FIX data in JSON format, stores it in the database,
        publishes it to RabbitMQ, and returns a success response.
        """
        try:
            data = request.get_json(silent=True)
            if not data:
                logger.error("Received invalid JSON")
                return jsonify({"status": "error", "message": "Invalid JSON"}), 400

            # Set the ingested timestamp if not provided
            ingested_ts = datetime.datetime.now(datetime.timezone.utc)
            data.setdefault("ingested_timestamp", ingested_ts.isoformat())

            # Ensure an order_id is present; generate one if necessary
            order_id = data.get("order_id")
            if not order_id:
                logger.error("order_id is missing from data")
                return jsonify({"status": "error", "message": "order_id is required"}), 400

            # Create and store the Order instance
            order = Order(
                order_id=order_id,
                ingested_timestamp=ingested_ts,
                additional_data=data  # Storing the full order JSON
            )
            db.session.add(order)
            db.session.commit()
            logger.info(f"Order stored in DB: {data}")

            # Publish the order to RabbitMQ
            try:
                publish_order(data)
                logger.info(f"Order published to RabbitMQ: {order_id}")
            except Exception as pub_err:
                logger.error(f"Failed to publish order to RabbitMQ: {pub_err}")

            return jsonify({"status": "success", "message": "Order ingested"}), 200

        except Exception as e:
            logger.error(f"Error in receive_order: {e}")
            return jsonify({"status": "error", "message": "Internal server error"}), 500

    @app.route('/orders', methods=['GET'])
    def list_orders():
        try:
            orders = Order.query.all()
            orders_list = [order.to_dict() for order in orders]
            return jsonify({"status": "success", "orders": orders_list}), 200
        except Exception as e:
            logger.error(f"Error in list_orders: {e}")
            return jsonify({"status": "error", "message": "Internal server error"}), 500

    @app.route('/orders/<order_id>', methods=['DELETE'])
    def delete_order(order_id):
        try:
            order = Order.query.filter_by(order_id=order_id).first()
            if order:
                db.session.delete(order)
                db.session.commit()
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
            orders = Order.query.order_by(Order.ingested_timestamp).all()
            logs = [
                f"Order {order.order_id} ingested at {order.ingested_timestamp.isoformat()}"
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
        if path and os.path.exists(file_path):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, 'index.html')

    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get("PORT", 5002))
    app.run(host="0.0.0.0", port=port, debug=False)