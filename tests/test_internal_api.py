import json
import pytest
from internal_api import app, orders

@pytest.fixture
def client():
    # Set up the Flask test client.
    app.config['TESTING'] = True
    with app.test_client() as client:
        # Before each test, clear the orders store.
        orders.clear()
        yield client

def test_receive_order_success(client):
    """
    Test that a valid POST to /orders returns a success response and stores the order.
    """
    # Sample enriched order data.
    sample_order = {
        "order_id": "ORDER123",
        "symbol": "BOND_XYZ",
        "quantity": 100,
        "price": 101.50,
        "business_unit": "BU-001",
        "trader_id": "TRADER001",
        "risk_category": "LOW",
        "processed_timestamp": "2025-02-14T12:00:00Z"
    }
    
    response = client.post('/orders', data=json.dumps(sample_order), content_type='application/json')
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data["status"] == "success"
    # Verify that the order was stored.
    assert len(orders) == 1
    assert orders[0]["order_id"] == "ORDER123"
    # Check that an ingested_timestamp is added.
    assert "ingested_timestamp" in orders[0]

def test_receive_order_invalid_json(client):
    """
    Test that sending invalid JSON returns an error.
    """
    response = client.post('/orders', data="not a json", content_type='application/json')
    data = json.loads(response.data)
    
    assert response.status_code == 400
    assert data["status"] == "error"

def test_list_orders(client):
    """
    Test that the GET /orders endpoint returns the stored orders.
    """
    # Pre-populate the in-memory store.
    orders.append({
        "order_id": "ORDER456",
        "symbol": "STOCK_ABC",
        "quantity": 200,
        "price": 50.25,
        "business_unit": "BU-001",
        "trader_id": "TRADER001",
        "risk_category": "LOW",
        "processed_timestamp": "2025-02-14T12:30:00Z",
        "ingested_timestamp": "2025-02-14T12:31:00Z"
    })
    response = client.get('/orders')
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data["status"] == "success"
    assert len(data["orders"]) == 1
    assert data["orders"][0]["order_id"] == "ORDER456"