import unittest


class TestConversions(unittest.TestCase):
    """Test cases for ascii <-> bytes conversions and the checksum."""

    def test_calculate_checksum(self):
        """
        Test the calculation of a checksum over data.
        """
        from btcp.btcp_socket import calculate_checksum

        self.assertEqual(calculate_checksum(b'\x00\x01\xf2\x03\xf4\xf5\xf6\xf7'), b'\x22\x0d')

    def test_validate_checksum(self):
        """
        Test if the validation of a checksum over data is correct.
        """
        from btcp.btcp_socket import valid_checksum, calculate_checksum

        # Create an artificial packet and calculate the checksum over it. Even length packet.
        packet = b'\x01\x23\x45\x67\x89\xab\xcd\xef\x00\x00\xff\xee\xdd\xcc\xbb\xaa'
        checksum = calculate_checksum(packet)
        packet = b'\x01\x23\x45\x67\x89\xab\xcd\xef' + checksum + b'\xff\xee\xdd\xcc\xbb\xaa'
        self.assertTrue(valid_checksum(packet))

        # Create an artificial packet and calculate the checksum over it. Uneven length packet.
        packet = b'\x01\x23\x45\x67\x89\xab\xcd\xef\x00\x00\xff\xee\xdd\xcc\xbb\xaa\x99'
        checksum = calculate_checksum(packet)
        packet = b'\x01\x23\x45\x67\x89\xab\xcd\xef' + checksum + b'\xff\xee\xdd\xcc\xbb\xaa\x99'
        self.assertTrue(valid_checksum(packet))

        # Create an artificial packet and calculate the checksum over it. Even length packet. Bit flip.
        packet = b'\x01\x23\x45\x67\x89\xab\xcd\xef\x00\x00\xff\xee\xdd\xcc\xbb\xaa\x99'
        checksum = calculate_checksum(packet)
        packet = b'\x00\x23\x45\x67\x89\xab\xcd\xef' + checksum + b'\xff\xee\xdd\xcc\xbb\xaa\x99'
        self.assertFalse(valid_checksum(packet))

    def test_flags_array_to_byte(self):
        """
        Test the transformation of the flags from ascii to bytes.
        """
        from btcp.btcp_socket import flags_array_to_byte

        # Test for an error when to many flags are given.
        with self.assertRaises(ValueError):
            flags_array_to_byte([True] * 9)

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
        from btcp.btcp_socket import ascii_to_bytes
        import btcp.constants

        self.assertEqual(ascii_to_bytes(100, 200, [True, False, True], 5, b'\x01\x23\x45\x67\x89'),
                         b'\x00d\x00\xc8\x05\x05\x00\x05*?\x01#Eg\x89')

        with self.assertRaises(ValueError):
            ascii_to_bytes(-1, 0, [True] * 3, 0, b'')
        with self.assertRaises(ValueError):
            ascii_to_bytes(65536, 0, [True] * 3, 0, b'')
        with self.assertRaises(ValueError):
            ascii_to_bytes(0, 0, [True] * 9, 0, b'')
        with self.assertRaises(ValueError):
            ascii_to_bytes(0, 0, [True, True], 0, b'')
        with self.assertRaises(ValueError):
            ascii_to_bytes(0, 0, [True] * 3, 256, b'')
        with self.assertRaises(ValueError):
            ascii_to_bytes(0, 0, [True] * 3, 0, b'\x00' * (btcp.constants.PAYLOAD_SIZE + 1))

    def test_bytes_to_ascii(self):
        """
         Test the transformation of the packets from bytes to ascii.
        """
        from btcp.btcp_socket import ascii_to_bytes, bytes_to_ascii
        import btcp.constants

        cases = [
            (0, 0, [False] * 3, 0, b''),
            (65535, 65535, [True] * 3, 255, b'\x00' * btcp.constants.PAYLOAD_SIZE),
            (32143, 432, [True, False, True], 123, b'\x98' * 543)
        ]
        for case in cases:
            segment = ascii_to_bytes(case[0], case[1], case[2], case[3], case[4])
            self.assertEqual(bytes_to_ascii(segment), case)

        for case in cases:
            segment = ascii_to_bytes(case[0], case[1], case[2], case[3], case[4])
            segment = segment[:3] + b'\x12' + segment[4:]
            with self.assertRaises(ValueError):
                bytes_to_ascii(segment)

    def test_create_segments(self):
        """
        Test if the data is chopped into correct segments.
        """
        from btcp.client_socket import BTCPClientSocket
        create_segments = BTCPClientSocket._create_segments

        data = b'\x00' * 1008 + b'\x01' * 1008 + b'\x02' * 1008 + b'\x03' * 50
        isn = 10
        segments = create_segments(data, isn)
        correct = [b'\x00\n\x00\x00\x00\x00\x03\xf0\xfc\x05' + b'\x00' * 1008,
                   b'\x00\x0b\x00\x00\x00\x00\x03\xf0\x02\x0b' + b'\x01' * 1008,
                   b'\x00\x0c\x00\x00\x00\x00\x03\xf0\x08\x10' + b'\x02' * 1008,
                   b'\x00\r\x00\x00\x00\x00\x002\xb4u' + b'\x03' * 50]
        self.assertEqual(segments, correct)


if __name__ == "__main__":
    unittest.main()
