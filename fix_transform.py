import json
import datetime

# Mapping dictionary: FIX tag to internal field name.
FIX_TO_INTERNAL_MAP = {
    11: "order_id",
    55: "symbol",
    38: "quantity",
    44: "price",
    60: "transact_time",  # Additional FIX tag.
}

# Default values for missing fields.
DEFAULTS = {
    "order_id": "UNKNOWN",
    "symbol": "N/A",
    "quantity": 0,
    "price": 0.0,
    "transact_time": None,
}

def transform_fix_to_json(fix_message):
    """
    Transforms a parsed FIX message (an iterable of (tag, value) pairs)
    into a dictionary representing the internal data model. This function:
      - Maps FIX fields to internal field names.
      - Converts numeric fields to proper types.
      - Uses default values for missing fields.
      - Enriches the data with additional metadata.
    """
    data = {}
    
    # Map fields from FIX message.
    for tag, value in fix_message:
        # If the value is bytes, decode it.
        if isinstance(value, bytes):
            value = value.decode("ascii")
        if tag in FIX_TO_INTERNAL_MAP:
            field_name = FIX_TO_INTERNAL_MAP[tag]
            data[field_name] = value

    # Set default values for missing fields.
    for field, default in DEFAULTS.items():
        if field not in data:
            data[field] = default

    # Data type conversion for numeric fields.
    try:
        data["quantity"] = int(data["quantity"])
    except (ValueError, TypeError):
        data["quantity"] = DEFAULTS["quantity"]
    try:
        data["price"] = float(data["price"])
    except (ValueError, TypeError):
        data["price"] = DEFAULTS["price"]

    # Enrichment: add additional internal metadata.
    data["business_unit"] = "BU-001"      # Placeholder for internal business unit.
    data["trader_id"] = "TRADER001"        # Placeholder for trader ID.
    data["risk_category"] = "LOW"          # Placeholder for risk category.
    data["processed_timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    return data

def transform_fix_to_json_str(fix_message):
    """
    Returns a JSON string representation of the transformed FIX message.
    """
    data = transform_fix_to_json(fix_message)
    return json.dumps(data)