import json
import logging
import pytest
from rabbitmq_consumer import process_order

def test_process_order(caplog):
    test_order = {
        "order_id": "TEST456",
        "symbol": "TEST",
        "quantity": 20,
        "price": 199.99,
        "business_unit": "BU-TEST",
        "trader_id": "TRADER_TEST",
        "risk_category": "MEDIUM",
        "processed_timestamp": "2025-02-18T00:00:00Z"
    }
    with caplog.at_level(logging.INFO):
        process_order(test_order)
    assert any("Processing order: TEST456" in record.message for record in caplog.records)