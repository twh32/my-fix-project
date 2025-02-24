import json
import pytest
from internal_api import create_app, db

@pytest.fixture
def client():
    # Create a new app instance for testing.
    app = create_app()
    app.config['TESTING'] = True
    # Optionally, override the database URI for tests if needed:
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/test_db'
    with app.app_context():
        db.create_all()  # Create all tables for testing.
        test_client = app.test_client()
        yield test_client
        db.session.remove()
        db.drop_all()

def test_receive_order_success(client):
    sample_order = {
        "order_id": "ORDER001",
        "symbol": "BOND_XYZ",
        "quantity": 100,
        "price": 101.5,
        "business_unit": "BU-001",
        "trader_id": "TRADER001",
        "risk_category": "LOW",
        "processed_timestamp": "2025-02-14T12:00:00Z"
    }
    # POST the order.
    response = client.post("/orders", data=json.dumps(sample_order), content_type='application/json')
    data = response.get_json()
    assert response.status_code == 200
    assert data["status"] == "success"

    # Verify that the order was stored by fetching orders via GET.
    get_response = client.get("/orders")
    orders_data = get_response.get_json()["orders"]
    assert len(orders_data) == 1
    order = orders_data[0]
    assert order["order_id"] == "ORDER001"
    assert "ingested_timestamp" in order

def test_receive_order_invalid_json(client):
    response = client.post("/orders", data="not a json", content_type='application/json')
    data = response.get_json()
    assert response.status_code == 400
    assert data["status"] == "error"

def test_list_orders(client):
    # Create an order via the POST endpoint.
    sample_order = {
        "order_id": "ORDER002",
        "symbol": "STOCK_ABC",
        "quantity": 200,
        "price": 50.25,
        "business_unit": "BU-001",
        "trader_id": "TRADER001",
        "risk_category": "LOW",
        "processed_timestamp": "2025-02-14T12:30:00Z"
    }
    client.post("/orders", data=json.dumps(sample_order), content_type='application/json')
    
    # List orders via GET.
    response = client.get("/orders")
    data = response.get_json()
    assert response.status_code == 200
    assert data["status"] == "success"
    assert len(data["orders"]) == 1
    assert data["orders"][0]["order_id"] == "ORDER002"

def test_delete_order_success(client):
    sample_order = {
        "order_id": "ORDER002",
        "symbol": "STOCK_ABC",
        "quantity": 200,
        "price": 50.25,
        "business_unit": "BU-001",
        "trader_id": "TRADER001",
        "risk_category": "LOW",
        "processed_timestamp": "2025-02-14T12:30:00Z"
    }
    # Create the order.
    client.post("/orders", data=json.dumps(sample_order), content_type='application/json')
    
    # Delete the order.
    response = client.delete("/orders/ORDER002")
    data = response.get_json()
    assert response.status_code == 200
    assert data["status"] == "success"
    assert "deleted" in data["message"]
    
    # Verify the order was deleted.
    get_response = client.get("/orders")
    get_data = get_response.get_json()
    assert len(get_data["orders"]) == 0

def test_delete_order_not_found(client):
    response = client.delete("/orders/NON_EXISTENT")
    data = response.get_json()
    assert response.status_code == 404
    assert data["status"] == "error"
    assert "not found" in data["message"]