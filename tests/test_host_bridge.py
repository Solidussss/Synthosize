"""Host timing bridge contract, without requiring FL Studio."""
import json
import socket
import time
import unittest
from engine.host_bridge import HostBridge

class HostBridgeTests(unittest.TestCase):
    def setUp(self):
        self.bridge = HostBridge(port=0)
        self.address = self.bridge._socket.getsockname()
        self.sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def tearDown(self):
        self.sender.close()
        self.bridge.close()

    def deliver(self, payload):
        self.sender.sendto(payload, self.address)
        for _ in range(100):
            if self.bridge.snapshot().get("connected"):
                break
            time.sleep(0.005)

    def test_disconnected_initially(self):
        self.assertEqual(self.bridge.snapshot(), {"connected": False})

    def test_valid_playback(self):
        self.deliver(json.dumps({"bpm": 142.5, "ppq": 17.5, "playing": True}).encode())
        self.assertEqual(self.bridge.snapshot(), {
            "connected": True, "bpm": 142.5, "ppq": 17.5, "playing": True})

    def test_bad_payload_ignored(self):
        self.deliver(b'{"bpm": -1, "ppq": 20, "playing": true}')
        self.assertEqual(self.bridge.snapshot(), {"connected": False})
        self.deliver(b"not-json")
        self.assertEqual(self.bridge.snapshot(), {"connected": False})

if __name__ == "__main__":
    unittest.main()
