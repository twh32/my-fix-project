import simplefix

def create_fix_message():
    # Create a new FIX message instance and add standard fields.
    msg = simplefix.FixMessage()
    msg.append_pair(8, "FIX.4.2")         # BeginString
    msg.append_pair(35, "A")              # MsgType: Logon
    msg.append_pair(49, "SENDER")         # SenderCompID
    msg.append_pair(56, "TARGET")         # TargetCompID
    msg.append_utc_timestamp(52)          # SendingTime
    msg.append_pair(98, "0")              # EncryptMethod (0 = None)
    msg.append_pair(108, "30")            # HeartBtInt
    return msg.encode()

def parse_fix_message(encoded_message):
    # Initialize the FIX parser and feed it the encoded message.
    parser = simplefix.FixParser()
    parser.append_buffer(encoded_message)
    
    # Retrieve the complete FIX message (if available).
    parsed_msg = parser.get_message()
    if parsed_msg is None:
        print("No complete FIX message found.")
        return None
    # Instead of accessing a 'fields' attribute, we can iterate directly.
    return list(parsed_msg)  # This converts the iterable into a list of (tag, value) pairs.

if __name__ == "__main__":
    # Create and encode the FIX message.
    encoded = create_fix_message()
    
    # For display purposes, replace the non-printable SOH (0x01) with a pipe.
    # Since simplefix does not provide a SOH constant, we use "\x01"
    readable = encoded.decode("ascii").replace("\x01", "|")
    print("Encoded FIX message:")
    print(readable)
    
    # Parse the message.
    fields = parse_fix_message(encoded)
    if fields:
        print("\nParsed FIX message fields:")
        for tag, value in fields:
            print(f"Tag {tag}: {value}")
