from btcp.lossy_layer import LossyLayer
from btcp.constants import *
from btcp.btcp_socket import ascii_to_bytes, bytes_to_ascii, merge_segments
import random
import threading


# A server application makes use of the services provided by bTCP by calling accept, recv, and close.
class BTCPServerSocket:

    def __init__(self, window_size):
        self._lossy_layer = LossyLayer(self, SERVER_IP, SERVER_PORT, CLIENT_IP, CLIENT_PORT)

        self._window_size = window_size  # The window size of this server.
        self._seq_num_server = None      # The sequence number for this server (practically ignored).
        self._seq_num_client = None      # The sequence number from the client (practically ignored).

        # Variables for receiving data from the client.
        self._data = None                # Tuples with (seq_num, data bytes) which are received.
        self._buffer = None              # Contains sequence numbers which need to be send back an ACK for.
        self._thread_ack = None          # This thread sends back ACKs for the sequence numbers in the buffer.

        # Variables for the connection establishment phase.
        self._connected_flag = None      # An event to signify when the connection is established.

        # Variables for the connection termination phase.
        self._finished_flag = None       # An event to signify when the connection is finished.

    # Called by the lossy layer from another thread whenever a segment arrives
    def lossy_layer_input(self, segment):
        try:
            seq_num, ack_num, flags, window_size, data = bytes_to_ascii(segment)
            if   flags[0]:  # ACK
                self._handle_ack(seq_num, ack_num)
            elif flags[1]:  # SYN
                self._handle_syn(seq_num)
            elif flags[2]:  # FIN
                self._handle_fin()
            else:           # DATA
                self._handle_data(seq_num, data)
        except ValueError:  # Incorrect checksum or data length.
            pass

    # Wait for the client to initiate a three-way handshake
    def accept(self):
        self._connected_flag = threading.Event()
        self._connected_flag.wait()

    # Send any incoming data to the application layer
    def recv(self):
        self._finished_flag = threading.Event()
        self._data = []
        self._buffer = []

        # Start emptying the buffer by sending back ACKs.
        self._thread_ack = threading.Thread(target=self._handle_buffer)
        self._thread_ack.start()

        # Wait until the final handshake is done.
        self._finished_flag.wait()
        self._thread_ack.join()  # Stop with sending back ACKs.

        # Merge all the received data together in the correct order.
        data = merge_segments(self._data)
        return data.decode()

    # Clean up any state
    def close(self):
        self._lossy_layer.destroy()

    def _handle_syn(self, seq_num):
        self._seq_num_client = seq_num
        self._seq_num_server = random.randint(0, 255)
        segment = ascii_to_bytes(self._seq_num_server, seq_num + 1, [True, True, False], self._window_size, b'')
        self._lossy_layer.send_segment(segment)

    def _handle_ack(self, seq_num, ack_num):
        if seq_num == self._seq_num_client + 1 and ack_num == self._seq_num_server + 1:
            self._seq_num_client += 1
            self._seq_num_server += 1
            self._connected_flag.set()

    def _handle_fin(self):
        segment = ascii_to_bytes(0, 0, [True, False, True], 0, b'')
        self._lossy_layer.send_segment(segment)
        self._finished_flag.set()

    def _handle_data(self, seq_num, data):
        self._buffer.append(seq_num)
        self._data.append((seq_num, data))

    def _handle_buffer(self):
        while not self._finished_flag.is_set():
            if len(self._buffer) > 0:
                seq_num = self._buffer.pop(0)
                segment = ascii_to_bytes(0, seq_num, [True, False, False], self._window_size - len(self._buffer), b'')
                self._lossy_layer.send_segment(segment)
