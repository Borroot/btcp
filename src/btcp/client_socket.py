from btcp.lossy_layer import LossyLayer
from btcp.constants import *
from btcp.btcp_socket import ascii_to_bytes, bytes_to_ascii
import random
import threading


# A client application makes use of the services provided by bTCP by calling connect, send, disconnect, and close.
class BTCPClientSocket:

    def __init__(self, timeout):
        self._lossy_layer = LossyLayer(self, CLIENT_IP, CLIENT_PORT, SERVER_IP, SERVER_PORT)

        self._timeout = timeout   # The timeout for one segment.
        self._timer   = None      # The timer used to detect a timeout.

        self._window_size = None  # The window size of the server.
        self._seq_num     = None  # The current sequence number.

        # Variables for the connection establishment phase.
        self._tries = None           # The number of tries to establish a connection.
        self._connected = None       # A boolean to signify if the connection was successful, returned by connect().
        self._connected_flag = None  # An event to signify when the connection is established.

    # Called by the lossy layer from another thread whenever a segment arrives. 
    def lossy_layer_input(self, segment):
        try:
            seq_num, ack_num, flags, window_size, data = bytes_to_ascii(segment)
            if   flags[0] and flags[1]:  # ACK & SYN
                self._handle_syn(seq_num, ack_num, window_size)
            elif flags[0]:  # ACK
                pass
            elif flags[2]:  # FIN
                pass
        except ValueError:  # Incorrect checksum or data length.
            pass

    # Perform a three-way handshake to establish a connection.
    def connect(self):
        # Create the initial sequence number and amount of tries to establish a connection and the connected flag.
        self._connected_flag = threading.Event()
        self._connected = False
        self._tries = 10
        self._seq_num = random.randint(0, 0xffff)

        # Send the first segment to the server.
        segment = ascii_to_bytes(self._seq_num, 0, [False, True, False], 0, b'')
        self._lossy_layer.send_segment(segment)

        # Create and start a timer for the connection establishment phase.
        self._timer = threading.Timer(self._timeout, self._handle_syn_timeout)
        self._timer.start()

        # Wait until the connection is established.
        self._connected_flag.wait()
        return self._connected

    # Send data originating from the application in a reliable way to the server.
    def send(self, data):
        pass

    # Perform a handshake to terminate a connection.
    def disconnect(self):
        pass

    # Clean up any state.
    def close(self):
        self._lossy_layer.destroy()

    def _handle_syn(self, seq_num, ack_num, window_size):
        if ack_num == self._seq_num + 1:
            self._timer.cancel()
            self._window_size = window_size
            self._seq_num += 1

            # Send an ACK back to the server.
            segment = ascii_to_bytes(self._seq_num, seq_num + 1, [True, False, False], 0, b'')
            self._lossy_layer.send_segment(segment)

            # Signal the connect() function that the connection is established.
            self._connected = True
            self._connected_flag.set()

    def _handle_syn_timeout(self):
        if self._tries <= 0:
            # Signal the connect() function that the connection could not be established.
            self._connected_flag.set()
        else:
            self._tries -= 1

            # Resend the initial segment.
            segment = ascii_to_bytes(self._seq_num, 0, [False, True, False], 0, b'')
            self._lossy_layer.send_segment(segment)

            # Restart the timeout timer.
            self._timer = threading.Timer(self._timeout, self._handle_syn_timeout)
            self._timer.start()


















