import json
import pytest
from internal_api import app, orders

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        # Clear orders before each test.
        orders.clear()
        yield client

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
    
    response = client.post("/orders", data=json.dumps(sample_order), content_type='application/json')
    data = response.get_json()
    
    assert response.status_code == 200
    assert data["status"] == "success"
    # Verify that the order was stored.
    assert len(orders) == 1
    assert orders[0]["order_id"] == "ORDER001"
    assert "ingested_timestamp" in orders[0]

def test_receive_order_invalid_json(client):
    response = client.post("/orders", data="not a json", content_type='application/json')
    data = response.get_json()
    
    assert response.status_code == 400
    assert data["status"] == "error"

def test_list_orders(client):
    orders.append({
        "order_id": "ORDER002",
        "symbol": "STOCK_ABC",
        "quantity": 200,
        "price": 50.25,
        "business_unit": "BU-001",
        "trader_id": "TRADER001",
        "risk_category": "LOW",
        "processed_timestamp": "2025-02-14T12:30:00Z",
        "ingested_timestamp": "2025-02-14T12:31:00Z"
    })
    response = client.get("/orders")
    data = response.get_json()
    
    assert response.status_code == 200
    assert data["status"] == "success"
    assert len(data["orders"]) == 1
    assert data["orders"][0]["order_id"] == "ORDER002"

def test_delete_order_success(client):
    """
    Test that deleting an existing order returns a success response and removes the order.
    """
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
    # Post the order.
    client.post("/orders", data=json.dumps(sample_order), content_type='application/json')
    
    # Delete the order.
    response = client.delete("/orders/ORDER002")
    data = response.get_json()
    
    assert response.status_code == 200
    assert data["status"] == "success"
    assert "deleted" in data["message"]
    
    # Verify that the orders list is empty by making a GET request.
    get_response = client.get("/orders")
    get_data = get_response.get_json()
    assert len(get_data["orders"]) == 0

def test_delete_order_not_found(client):
    """
    Test that attempting to delete a non-existent order returns an error.
    """
    response = client.delete("/orders/NON_EXISTENT")
    data = response.get_json()
    
    assert response.status_code == 404
    assert data["status"] == "error"
    assert "not found" in data["message"]