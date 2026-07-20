from dataclasses import dataclass
import time
@dataclass
class Scanner:
    channels: list
    index: int = -1
    active: bool = False
    dwell_seconds: int = 5
    _due: float = 0
    def start(self, now=None):
        if not self.channels: raise ValueError("A lista do scanner está vazia.")
        self.active = True
        self._due = time.monotonic() if now is None else now
    def stop(self): self.active = False
    def next_channel(self):
        if not self.active: return None
        self.index = (self.index + 1) % len(self.channels)
        return self.channels[self.index]
    def tick(self, now=None):
        now = time.monotonic() if now is None else now
        if not self.active or now < self._due:
            return None
        self._due = now + self.dwell_seconds
        return self.next_channel()
