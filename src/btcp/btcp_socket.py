
def checksum(data):
    pass


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


def ascii_to_bytes(seq_num, ack_num, flags, window_size, data_length, checksum, data):
    """
    Create a packet from the data that is given.
    :param flags: Boolean array containing flags as follows [ACK,SYN,FIN].
    :return: A bytes packet.
    """
    header  = seq_num.to_bytes(2, byteorder='big')
    header += ack_num.to_bytes(2, byteorder='big')
    header += flags_array_to_byte(flags)
    header += window_size.to_bytes(1, byteorder='big')
    header += data_length.to_bytes(2, byteorder='big')
    header += b'\x00\x00'  # TODO: calculate the checksum
    return header + data.encode()


def bytes_to_ascii(packet):
    """
    Extract all of the data values from a packet.
    :return: All the data values.
    """
    pass
    # return seq_num, ack_num, flags, window_size, data_length, checksum, data

