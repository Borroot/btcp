from btcp.lossy_layer import LossyLayer
from btcp.constants import *
from btcp.btcp_socket import ascii_to_bytes, bytes_to_ascii, create_segments
import time
import random
import threading


# A client application makes use of the services provided by bTCP by calling connect, send, disconnect, and close.
class BTCPClientSocket:

    def __init__(self, timeout):
        self._lossy_layer = LossyLayer(self, CLIENT_IP, CLIENT_PORT, SERVER_IP, SERVER_PORT)

        self._timeout = timeout / 100000  # The timeout for one segment in seconds.
        self._timer   = None              # The timer used to detect a timeout.
        self._seq_num = None              # The initial sequence number, initialized during establishment.

        # Variables for sending data over to the server.
        self._send_flag = None     # A flag to signify when to stop all the threads.
        self._seg_tries = None     # The amount of tries every segment gets.

        self._segments = None      # All segments which are to be send plus the amount of tries left for every segment.
        self._status   = None      # The status for every segment: 0 not send, 1 send not ACKed, 2 timeout, 3 ACKed.
        self._pending  = None      # The time at which certain segments are send, contains (seq_num, time send).

        self._send_base   = None   # The index for self._segments up to which all segments are ACKed.
        self._window_size = None   # The window size of the server, initialized during establishment.

        self._status_lock  = None  # Ensure that changing the status list is done thread safe.
        self._pending_lock = None  # Ensure that changing the pending list is done thread safe.
        self._send_base_lock = None  # Ensure that changing the send base is done thread safe.

        # Variables for the connection establishment phase.
        self._syn_tries = None         # The number of tries to establish a connection.
        self._connected = None         # A boolean to signify if the connection was successful, returned by connect().
        self._connected_flag = None    # An event to signify when the connection is established.

        # Variables for the connection termination phase.
        self._fin_tries = None         # The number of tries to terminate a connection.
        self._finished = None          # A boolean to signify if the closing was (ab)normal, returned by disconnect().
        self._finished_flag = None     # An event to signify when the connection is terminated.

    # Called by the lossy layer from another thread whenever a segment arrives. 
    def lossy_layer_input(self, segment):
        try:
            seq_num, ack_num, flags, window_size, data = bytes_to_ascii(segment)
            if   flags[0] and flags[1]:  # ACK & SYN
                self._handle_syn(seq_num, ack_num, window_size)
            elif flags[0] and flags[2]:  # ACK & FIN
                self._handle_fin()
            elif flags[0]:  # ACK
                self._handle_ack(ack_num, window_size)
        except ValueError:  # Incorrect checksum or data length.
            pass

    # Perform a three-way handshake to establish a connection.
    def connect(self):
        # Create the initial sequence number and amount of tries to establish a connection and the connected flag.
        self._connected_flag = threading.Event()
        self._connected = False
        self._syn_tries = 30
        self._seq_num = random.randint(0, 0xffff)

        # Send the first segment to the server.
        segment = ascii_to_bytes(self._seq_num, 0, [False, True, False], 0, b'')
        self._lossy_layer.send_segment(segment)

        # Create and start a timer for the connection establishment phase.
        self._timer = threading.Timer(self._timeout, self._handle_syn_timeout)
        self._timer.start()

        # Wait until the connection handshake is done.
        self._connected_flag.wait()
        return self._connected

    # Send data originating from the application in a reliable way to the server.
    def send(self, data):
        data = data.encode()

        # Initialize all the variables.
        self._send_flag = threading.Event()
        self._seg_tries = 30
        self._send_base = 0

        self._segments = [[segment, self._seg_tries] for segment in create_segments(data, self._seq_num)]
        self._status   = [0] * len(self._segments)
        self._pending  = []

        self._status_lock  = threading.Lock()
        self._pending_lock = threading.Lock()
        self._send_base_lock = threading.Lock()

        # Start the timer in a new thread.
        self._timer = threading.Thread(target=self._timer_loop)
        self._timer.start()

        # Send all of the segments, returns if all are send.
        success = self._send_loop()

        # Set the _send_flag so the timer will stop.
        self._send_flag.set()
        self._timer.join()

        # Return if the sending of all the segments was successful.
        return success

    # Perform a handshake to terminate a connection.
    def disconnect(self):
        self._finished_flag = threading.Event()
        self._finished = False
        self._fin_tries = 15

        # Send a FIN to the server.
        segment = ascii_to_bytes(0, 0, [False, False, True], 0, b'')
        self._lossy_layer.send_segment(segment)

        # Create and start a timer for the connection termination phase.
        self._timer = threading.Timer(self._timeout, self._handle_fin_timeout)
        self._timer.start()

        # Wait until the termination handshake is done.
        self._finished_flag.wait()
        return self._finished

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
        if self._syn_tries <= 0:
            # Signal the connect() function that the connection could not be established.
            self._connected_flag.set()
        else:
            self._syn_tries -= 1

            # Resend the initial segment.
            segment = ascii_to_bytes(self._seq_num, 0, [False, True, False], 0, b'')
            self._lossy_layer.send_segment(segment)

            # Restart the timeout timer.
            self._timer = threading.Timer(self._timeout, self._handle_syn_timeout)
            self._timer.start()

    def _handle_fin(self):
        self._timer.cancel()
        self._finished = True
        self._finished_flag.set()

    def _handle_fin_timeout(self):
        if self._fin_tries <= 0:
            # Signal the disconnect() function that the connection could not be normally terminated.
            self._finished_flag.set()
        else:
            self._fin_tries -= 1

            # Resend the initial segment.
            segment = ascii_to_bytes(0, 0, [False, False, True], 0, b'')
            self._lossy_layer.send_segment(segment)

            # Restart the timeout timer.
            self._timer = threading.Timer(self._timeout, self._handle_fin_timeout)
            self._timer.start()

    def _handle_ack(self, ack_num, window_size):
        # Update the window size and increase the send base by one if this was the next to be ACKed segment.
        self._window_size = window_size
        try:
            self._send_base_lock.acquire()
            if self._send_base == ack_num - self._seq_num:
                self._send_base = ack_num - self._seq_num + 1
        finally:
            self._send_base_lock.release()

        # Change the segment status to received ACK.
        try:
            self._status_lock.acquire()
            self._status[ack_num - self._seq_num] = 3  # ACKed flag
        finally:
            self._status_lock.release()

        # Remove the ACKed segment from the pending list.
        try:
            self._pending_lock.acquire()
            self._pending = [(seq_num, _time) for (seq_num, _time) in self._pending if seq_num != ack_num]
        finally:
            self._pending_lock.release()

    def _timer_loop(self):
        while not self._send_flag.is_set():
            try:
                self._status_lock.acquire()
                self._pending_lock.acquire()
                still_pending = []
                for (seq_num, time_send) in self._pending:
                    if time.time_ns() // 1000 - time_send > self._timeout * 100000:
                        # A timeout occurred, change the status flag to timeout so it will be resend.
                        if self._status[self._seq_num - seq_num] != 3:  # not ACKed
                            self._status[self._seq_num - seq_num] = 2  # timeout flag
                    else:
                        still_pending.append((seq_num, time_send))
                self._pending = still_pending
            finally:
                self._pending_lock.release()
                self._status_lock.release()
            time.sleep(0.005)

    def _send_loop(self):
        while self._send_base < len(self._segments):  # There are segments left to get ACKed.
            # Check all the segments from the send base till the window if one can be send and then send ONE or none.
            try:
                self._send_base_lock.acquire()
                self._status_lock.acquire()
                for index, status in enumerate(self._status[self._send_base:self._send_base + self._window_size]):
                    if (status == 0 or status == 2) and len(self._pending) < self._window_size:  # not send or timeout
                        # Check if the amount of tries for this segment is exceeded.
                        if self._segments[self._send_base + index][1] <= 0:
                            return False
                        else:
                            self._segments[self._send_base + index][1] -= 1

                        # Send the segment, add it to the pending segments and update the status.
                        self._lossy_layer.send_segment(self._segments[self._send_base + index][0])
                        self._status[self._send_base + index] = 1  # send but not ACKed flag
                        try:
                            self._pending_lock.acquire()
                            self._pending.append((self._send_base + index + self._seq_num, time.time_ns() // 1000))
                        finally:
                            self._pending_lock.release()
            finally:
                self._status_lock.release()
                self._send_base_lock.release()
        return True
