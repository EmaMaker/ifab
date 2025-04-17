import socket

# socket setup

CLIENT_1 = "ifab.local"
CLIENT_PORT = 4242
MESSAGE = b"""
{
    "robot": [
        1.1,
        2.2,
        3.3
    ],
    "target": [
        4.4,
        5.5,
        6.6
    ]
}
"""

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(MESSAGE, (CLIENT_1, CLIENT_PORT))
