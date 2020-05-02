from btcp.lossy_layer import LossyLayer
from btcp.constants import *


# The bTCP server socket
# A server application makes use of the services provided by bTCP by calling accept, recv, and close
class BTCPServerSocket:

    def __init__(self, window):
        self._lossy_layer = LossyLayer(self, SERVER_IP, SERVER_PORT, CLIENT_IP, CLIENT_PORT)

    # Called by the lossy layer from another thread whenever a segment arrives
    def lossy_layer_input(self, segment):
        pass

    # Wait for the client to initiate a three-way handshake
    def accept(self):
        pass

    # Send any incoming data to the application layer
    def recv(self):
        pass

    # Clean up any state
    def close(self):
        self._lossy_layer.destroy()
