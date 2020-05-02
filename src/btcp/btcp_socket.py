import struct
import btcp.constants


def calculate_checksum(segment):
    """
    Calculate the Internet Checksum as defined by RFC 1071. If the data is not divisible by 16 bits then the data is
    padded with zeros until it is.
    :return: The Internet Checksum computed over the given data (with padding).
    """
    if len(segment) % 2 != 0:
        segment += b'\x00'

    checksum = 0
    for pair in range(0, len(segment), 2):
        current = (segment[pair] << 8) + segment[pair + 1]
        if checksum + current >= 2**16:
            checksum = (checksum + current) % 2**16 + 1
        else:
            checksum += current
    checksum = checksum ^ 0xffff
    return checksum.to_bytes(2, byteorder='big')


def valid_checksum(segment):
    """
    Validate the Internet Checksum as defined by RFC 1071.
    :return: If the checksum is correct yes or no.
    """
    return calculate_checksum(segment) == b'\x00\x00'


def flags_array_to_byte(flags):
    """
    :param flags: Boolean array containing flags as follows [ACK,SYN,FIN].
    :return: A byte containing the flags in the first few bits.
    """
    if len(flags) > 8:
        raise ValueError("The maximum size of the flags array is 8, this is exceeded.")

    total = 0
    for index, flag in enumerate(flags):
        if flag:
            total += 1 * 2**index
    return total.to_bytes(1, byteorder='big')


def flags_byte_to_array(byte):
    """
    :param byte: Byte containing flags in the first few bits.
    :return: Boolean array containing the flags as follows [ACK,SYN,FIN].
    """
    if len(byte) != 1:
        raise ValueError("More or less than one byte are given.")

    total = int.from_bytes(byte, byteorder='big')
    flags = []
    for index in range(2, -1, -1):
        if total - (2**index) >= 0:
            flags.append(True)
            total -= 2**index
        else:
            flags.append(False)
    flags.reverse()
    return flags


def ascii_to_bytes(seq_num, ack_num, flags, window_size, data):
    """
    Create a segment from the data that is given. Note that the checksum and data length are calculated from this data.
    :param flags: Boolean array containing flags as follows [ACK,SYN,FIN].
    :param data: The data to be send, already as bytes (for easier data chopping with unicode characters).
    :return: A bytes segment.
    :raises ValueError: If one of the values is out of range.
    """
    if seq_num > 0xffff or seq_num < 0x0000:
        raise ValueError("The sequence number is out of range: {}.".format(seq_num))
    if ack_num > 0xffff or ack_num < 0x0000:
        raise ValueError("The acknowledgement number is out of range: {}.".format(ack_num))
    if len(flags) < 3 or len(flags) > 8:
        raise ValueError("The size of the flags array is out of range: {}.".format(len(flags)))
    if window_size > 0xff or window_size < 0x00:
        raise ValueError("The window size is out of range: {}.".format(window_size))
    if len(data) > btcp.constants.PAYLOAD_SIZE:
        raise ValueError("The data size is out of range: {}.".format(data))

    header  = seq_num.to_bytes(2, byteorder='big')
    header += ack_num.to_bytes(2, byteorder='big')
    header += flags_array_to_byte(flags)
    header += window_size.to_bytes(1, byteorder='big')
    header += len(data).to_bytes(2, byteorder='big')
    header += calculate_checksum(header + b'\x00\x00' + data)
    return header + data


def bytes_to_ascii(segment):
    """
    Extract all of the data values from a segment.
    :return: All the data values. The data value is of bytes and should only be decoded when all segments are received.
    :raises: ValueError If the checksum is not valid or if the data_length is different from the actual amount of data.
    """
    seq_num     = struct.unpack('>H', segment[0:2])[0]
    ack_num     = struct.unpack('>H', segment[2:4])[0]
    flags       = flags_byte_to_array(segment[4].to_bytes(1, byteorder='big'))
    window_size = struct.unpack('>B', segment[5].to_bytes(1, byteorder='big'))[0]
    data_length = struct.unpack('>H', segment[6:8])[0]
    data        = segment[10:]

    if len(data) != data_length:
        raise ValueError("The data length is not equal to the actual amount of data.")
    if not valid_checksum(segment):
        raise ValueError("The checksum is invalid.")

    return seq_num, ack_num, flags, window_size, data

