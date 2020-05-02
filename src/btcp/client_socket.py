from btcp.lossy_layer import LossyLayer
from btcp.constants import *
from btcp.btcp_socket import ascii_to_bytes
import random


# A client application makes use of the services provided by bTCP by calling connect, send, disconnect, and close.
class BTCPClientSocket:

    def __init__(self, timeout):
        self._lossy_layer = LossyLayer(self, CLIENT_IP, CLIENT_PORT, SERVER_IP, SERVER_PORT)

    # Called by the lossy layer from another thread whenever a segment arrives. 
    def lossy_layer_input(self, segment):
        pass

    # Perform a three-way handshake to establish a connection.
    def connect(self):
        seg_num = random.randint(0, 0xffff)
        segment = ascii_to_bytes(seg_num, 0, [False, True, False], 0, b'')
        self._lossy_layer.send_segment(segment)

    # Send data originating from the application in a reliable way to the server.
    def send(self, data):
        pass

    # Perform a handshake to terminate a connection.
    def disconnect(self):
        pass

    # Clean up any state.
    def close(self):
        self._lossy_layer.destroy()
