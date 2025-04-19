import socket

# socket setup

CLIENT_1 = "ifab.local"
CLIENT_PORT = 4242
# Posizioni in metri angoli in radianti
MESSAGE = b"""
{
'robot': {'x': 4.909115677648179, 'y': 15.008719473020381, 'theta': -0.09239503516195423},
'target': {'x': 5.909115677648179, 'y': 17.008719473020381,'theta': -0.19239503516195423}
}
"""

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(MESSAGE, (CLIENT_1, CLIENT_PORT))
