import simplefix
import time

# Global sequence number for outgoing messages
sequence_number = 1

def build_order_message(order_id, symbol, quantity, price):
    global sequence_number
    msg = simplefix.FixMessage()
    msg.append_pair(8, "FIX.4.2")
    msg.append_pair(35, "D")
    msg.append_pair(11, order_id)
    msg.append_pair(34, str(sequence_number))
    msg.append_pair(49, "SENDER")
    msg.append_pair(56, "TARGET")
    msg.append_utc_timestamp(52)
    msg.append_pair(55, symbol)
    msg.append_pair(38, quantity)
    msg.append_pair(44, price)
    msg.append_pair(98, "0")
    msg.append_pair(108, "30")
    sequence_number += 1
    return msg.encode()

def reset_sequence():
    global sequence_number
    sequence_number = 1