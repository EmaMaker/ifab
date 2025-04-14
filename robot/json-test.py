import socket

# socket setup

CLIENT_1 = "ifab.local"
CLIENT_PORT = 4242
MESSAGE = b"""
{
    "setpoint": [
        1.1,
        2.2,
        3.3
    ],
    "target": [
        4.4,
        5.5,
        6.6
    ],
    "target2": [
        7.7,
        8.8,
        9.9
    ]
}
"""

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(MESSAGE, (CLIENT_1, CLIENT_PORT))
