import simplefix

def validate_fix_message_fields(fields):
    # Define the required tags (you can adjust this list as needed)
    required_tags = [8, 9, 35, 49, 52, 56, 10]
    # Collect the tags present in the message
    present_tags = {tag for tag, value in fields}
    # Find any missing tags
    missing = [tag for tag in required_tags if tag not in present_tags]
    if missing:
        print("Missing required tags:", missing)
    else:
        print("All required tags are present.")

def create_order_message():
    # Build a New Order Single message representing a bond purchase.
    msg = simplefix.FixMessage()
    msg.append_pair(8, "FIX.4.2")         # BeginString
    msg.append_pair(35, "D")              # MsgType: New Order Single
    msg.append_pair(11, "ORDER123")       # ClOrdID (unique order ID)
    msg.append_pair(49, "SENDER")         # SenderCompID
    msg.append_pair(56, "TARGET")         # TargetCompID
    msg.append_utc_timestamp(52)          # SendingTime
    msg.append_pair(55, "BOND_XYZ")       # Symbol (bond identifier)
    msg.append_pair(38, "100")            # Order Quantity
    msg.append_pair(44, "101.50")         # Price
    msg.append_pair(98, "0")              # EncryptMethod (none)
    msg.append_pair(108, "30")            # HeartBtInt
    return msg.encode()

def main():
    # Create an order message and encode it.
    encoded = create_order_message()
    
    # For easier reading, replace the non-printable SOH (ASCII 0x01) delimiter with a pipe character.
    readable = encoded.decode("ascii").replace("\x01", "|")
    print("Encoded FIX message:")
    print(readable)
    
    # Parse the encoded message.
    parser = simplefix.FixParser()
    parser.append_buffer(encoded)
    msg = parser.get_message()
    if msg is None:
        print("No complete FIX message found.")
        return
    # Convert the message to a list of (tag, value) pairs.
    fields = list(msg)
    print("\nParsed FIX message fields:")
    for tag, value in fields:
        print(f"Tag {tag}: {value}")
    
    # Validate that all required tags are present.
    print()
    validate_fix_message_fields(fields)

if __name__ == "__main__":
    main()
