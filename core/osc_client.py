"""Minimal VRChat OSC sender. UDP is connectionless, so send != delivery confirmation."""
from __future__ import annotations

try:
    from pythonosc.udp_client import SimpleUDPClient
except ImportError:
    from core.simple_osc import SimpleUDPClient


class OSCClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 9000):
        self.host = host
        self.port = port
        self._client = SimpleUDPClient(host, port)

    def send_chatbox(self, message: str, *, notify: bool = True) -> None:
        if not message:
            raise ValueError("Cannot send an empty chatbox message")
        if len(message) > 144:
            raise ValueError("VRChat chatbox messages must be 144 characters or fewer")
        # First bool: send immediately. Second bool: play notification sound.
        self._client.send_message("/chatbox/input", [message, True, notify])

    def set_typing(self, typing: bool) -> None:
        self._client.send_message("/chatbox/typing", bool(typing))
