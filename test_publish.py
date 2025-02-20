from rabbitmq_publisher import publish_order

sample_order = {
    "order_id": "TEST_LOCAL",
    "symbol": "TEST",
    "quantity": 10,
    "price": 99.99,
    "business_unit": "BU-LOCAL",
    "trader_id": "TRADER_LOCAL",
    "risk_category": "LOW",
    "processed_timestamp": "2025-02-18T00:00:00Z"
}

publish_order(sample_order)
print("Order published successfully.")