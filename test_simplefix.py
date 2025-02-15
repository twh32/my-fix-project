import simplefix

# Create a new FIX message instance.
msg = simplefix.FixMessage()

# Build a simple Logon message.
msg.append_pair(8, "FIX.4.2")  # BeginString
msg.append_pair(35, "A")       # MsgType: Logon
msg.append_pair(49, "SENDER")  # SenderCompID
msg.append_pair(56, "TARGET")  # TargetCompID
msg.append_utc_timestamp(52)   # SendingTime
msg.append_pair(98, "0")       # EncryptMethod (0 = None)
msg.append_pair(108, "30")     # HeartBtInt

# Encode the message into bytes.
encoded = msg.encode()
print("Encoded FIX message:")
print(encoded.decode("ascii"))
