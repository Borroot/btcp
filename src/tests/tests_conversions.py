import unittest


class TestConversions(unittest.TestCase):
    """Test cases for ascii <-> bytes conversions."""

    def test_flags_array_to_byte(self):
        """
        Test the transformation of the flags from ascii to bytes.
        """
        from btcp.btcp_socket import flags_array_to_byte

        # Test for an error when to many flags are given.
        with self.assertRaises(ValueError):
            flags_array_to_byte([True, False, True, False, True, False, True, False, True])

        # Test for correct conversions.
        self.assertEqual(flags_array_to_byte([False, False, False]), b'\x00')
        self.assertEqual(flags_array_to_byte([True,  False, False]), b'\x01')
        self.assertEqual(flags_array_to_byte([False, True,  False]), b'\x02')
        self.assertEqual(flags_array_to_byte([True,  True,  False]), b'\x03')
        self.assertEqual(flags_array_to_byte([False, False, True]),  b'\x04')
        self.assertEqual(flags_array_to_byte([True,  False, True]),  b'\x05')
        self.assertEqual(flags_array_to_byte([False, True,  True]),  b'\x06')
        self.assertEqual(flags_array_to_byte([True,  True,  True]),  b'\x07')

    def test_flags_byte_to_array(self):
        """
        Test the transformation of the flags from ascii to bytes.
        """
        from btcp.btcp_socket import flags_byte_to_array

        # Test for an error when too many or too little bytes are given.
        with self.assertRaises(ValueError):
            flags_byte_to_array(b'\x00\x00')

        with self.assertRaises(ValueError):
            flags_byte_to_array(b'')

        # Test for correct conversions.
        self.assertEqual(flags_byte_to_array(b'\x00'), [False, False, False])
        self.assertEqual(flags_byte_to_array(b'\x01'), [True,  False, False])
        self.assertEqual(flags_byte_to_array(b'\x02'), [False, True,  False])
        self.assertEqual(flags_byte_to_array(b'\x03'), [True,  True,  False])
        self.assertEqual(flags_byte_to_array(b'\x04'), [False, False, True])
        self.assertEqual(flags_byte_to_array(b'\x05'), [True,  False, True])
        self.assertEqual(flags_byte_to_array(b'\x06'), [False, True,  True])
        self.assertEqual(flags_byte_to_array(b'\x07'), [True,  True,  True])

    def test_ascii_to_bytes(self):
        """
        Test the transformation of the packets from ascii to bytes.
        """
        pass

    def test_bytes_to_ascii(self):
        """
         Test the transformation of the packets from bytes to ascii.
        """
        pass


if __name__ == "__main__":
    unittest.main()
