import unittest
import simplefix
import time
from ..fix_core import build_order_message

class TestFixMessageFunctions(unittest.TestCase):
    def test_build_order_message(self):
        # Define sample order details.
        order_id = "TEST_ORDER"
        symbol = "BOND_XYZ"
        quantity = "100"
        price = "101.50"
        
        # Build the order message.
        msg_bytes = build_order_message(order_id, symbol, quantity, price)
        
        # Decode message and replace the non-printable SOH for readability.
        msg_str = msg_bytes.decode("ascii").replace("\x01", "|")
        
        # Assert that the message contains expected FIX tags and values.
        self.assertIn("8=FIX.4.2", msg_str)
        self.assertIn("35=D", msg_str)
        self.assertIn("11=TEST_ORDER", msg_str)
        self.assertIn("55=BOND_XYZ", msg_str)
        self.assertIn("38=100", msg_str)
        self.assertIn("44=101.50", msg_str)
        # Optionally, check for presence of a sequence number tag.
        self.assertIn("34=", msg_str)
    
    # You can add more tests here for parsing, transformation, etc.

if __name__ == "__main__":
    unittest.main()