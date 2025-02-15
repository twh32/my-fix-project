import pytest
import json
from ..fix_transform import transform_fix_to_json, transform_fix_to_json_str

def test_transform_with_all_fields():
    """
    Test transforming a FIX message that includes all expected fields.
    """
    # Sample FIX message with all fields provided.
    fix_message = [
        (11, b"ORDER123"),
        (55, b"BOND_XYZ"),
        (38, b"100"),
        (44, b"101.50"),
        (60, b"20250214-12:00:00"),
    ]
    
    result = transform_fix_to_json(fix_message)
    # Verify mapping.
    assert result["order_id"] == "ORDER123"
    assert result["symbol"] == "BOND_XYZ"
    # Numeric conversion: expect int and float.
    assert result["quantity"] == 100      # changed from "100" to 100
    assert result["price"] == 101.50        # remains a float
    assert result["transact_time"] == "20250214-12:00:00"
    # Verify enrichment.
    assert result["business_unit"] == "BU-001"
    assert result["trader_id"] == "TRADER001"  # if you add this enrichment later; adjust if needed
    assert result["risk_category"] == "LOW"    # if you add this enrichment later; adjust if needed
    assert "processed_timestamp" in result

def test_transform_with_missing_fields():
    """
    Test transforming a FIX message with missing fields.
    The missing fields should be filled with default values.
    """
    fix_message = [
        (55, b"STOCK_ABC"),
        (38, b"200"),
        (44, b"50.25"),
        # Missing tag 11 (order_id) and tag 60 (transact_time)
    ]
    result = transform_fix_to_json(fix_message)
    # Check that missing fields get default values.
    assert result["order_id"] == "UNKNOWN"
    assert result["transact_time"] is None
    # Check conversion of numeric fields.
    assert result["quantity"] == 200
    assert result["price"] == 50.25
    # Check enrichment.
    assert result["business_unit"] == "BU-001"
    assert result["trader_id"] == "TRADER001"
    assert result["risk_category"] == "LOW"
    assert "processed_timestamp" in result

def test_transform_invalid_numeric_fields():
    """
    Test that if numeric fields cannot be converted, default values are used.
    """
    fix_message = [
        (11, b"ORDER456"),
        (55, b"STOCK_DEF"),
        (38, b"not_a_number"),
        (44, b"invalid_price"),
    ]
    result = transform_fix_to_json(fix_message)
    # Check that conversion failures result in default numeric values.
    assert result["quantity"] == 0
    assert result["price"] == 0.0

def test_transform_to_json_str():
    """
    Test that the transformation to a JSON string works correctly.
    """
    fix_message = [
        (11, b"ORDER789"),
        (55, b"STOCK_GHI"),
        (38, b"300"),
        (44, b"75.00"),
    ]
    json_str = transform_fix_to_json_str(fix_message)
    data = json.loads(json_str)
    assert data["order_id"] == "ORDER789"
    assert data["symbol"] == "STOCK_GHI"
    # Expect numeric types.
    assert data["quantity"] == 300
    assert data["price"] == 75.00
    assert "business_unit" in data
    assert "trader_id" in data
    assert "risk_category" in data
    assert "processed_timestamp" in data