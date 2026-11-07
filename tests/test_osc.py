import importlib
import sys
import types
import pytest


def test_osc_payload(monkeypatch):
    sent = []
    osc_package = types.ModuleType("pythonosc")
    client_module = types.ModuleType("pythonosc.udp_client")

    class MockUDPClient:
        def __init__(self, host, port):
            assert (host, port) == ("127.0.0.1", 9000)

        def send_message(self, path, value):
            sent.append((path, value))

    client_module.SimpleUDPClient = MockUDPClient
    monkeypatch.setitem(sys.modules, "pythonosc", osc_package)
    monkeypatch.setitem(sys.modules, "pythonosc.udp_client", client_module)
    module = importlib.import_module("core.osc_client")
    client = module.OSCClient()
    client.send_chatbox("Testing", notify=False)
    client.set_typing(True)
    assert sent == [("/chatbox/input", ["Testing", True, False]), ("/chatbox/typing", True)]
    with pytest.raises(ValueError):
        client.send_chatbox("x" * 145)
