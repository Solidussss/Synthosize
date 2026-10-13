"""Local-only FL Studio transport bridge. Never handles project/media commands."""
import json
import socket
import threading
import time

PORT = 48383

class HostBridge:
    def __init__(self, port=PORT):
        self._lock = threading.Lock()
        self._last = None
        self._received = 0.0
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.bind(("127.0.0.1", port))
        threading.Thread(target=self._receive, daemon=True, name="synthosize-host-bridge").start()

    def _receive(self):
        while True:
            try:
                payload, source = self._socket.recvfrom(1024)
                if source[0] != "127.0.0.1":
                    continue
                state = json.loads(payload)
                bpm = float(state["bpm"])
                ppq = float(state["ppq"])
                playing = state["playing"]
                if not (20 <= bpm <= 400 and -100000 < ppq < 100000000 and type(playing) is bool):
                    continue
                with self._lock:
                    self._last = {"bpm": bpm, "ppq": ppq, "playing": playing}
                    self._received = time.monotonic()
            except (ValueError, KeyError, TypeError, OverflowError, UnicodeDecodeError):
                continue
            except OSError:
                break

    def close(self):
        self._socket.close()

    def snapshot(self):
        with self._lock:
            if self._last is None or time.monotonic() - self._received > 2:
                return {"connected": False}
            return {"connected": True, **self._last}
