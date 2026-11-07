"""Small, standalone Open Sound Control UDP encoder (OSC 1.0)."""
import socket
import struct

def _osc_string(value):
    data = value.encode('utf-8') + b'\0'
    return data + b'\0' * (-len(data) % 4)

def _osc_message(address, values):
    if isinstance(values, (str, bool, int, float)):
        values = [values]
    tags = ','
    body = b''
    for value in values:
        if isinstance(value, bool):
            tags += 'T' if value else 'F'
        elif isinstance(value, str):
            tags += 's'
            body += _osc_string(value)
        elif isinstance(value, int):
            tags += 'i'
            body += struct.pack('>i', value)
        elif isinstance(value, float):
            tags += 'f'
            body += struct.pack('>f', value)
        else:
            raise TypeError(f'Unsupported OSC value: {type(value).__name__}')
    return _osc_string(address) + _osc_string(tags) + body

class SimpleUDPClient:
    def __init__(self, host, port):
        self.host = host
        self.port = int(port)
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send_message(self, address, values):
        self._socket.sendto(_osc_message(address, values), (self.host, self.port))
