import socket
import time
# socket setup

CLIENT_1 = "10.42.0.18"
CLIENT_PORT = 4242
# Posizioni in metri angoli in radianti
MESSAGE = b"""
{
'face' : 2
}
"""

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(MESSAGE, (CLIENT_1, CLIENT_PORT))
