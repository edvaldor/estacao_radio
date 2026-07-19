from dataclasses import dataclass
@dataclass
class Scanner:
    channels: list
    index: int = -1
    active: bool = False
    def start(self):
        if not self.channels: raise ValueError("A lista do scanner está vazia.")
        self.active = True
    def stop(self): self.active = False
    def next_channel(self):
        if not self.active: return None
        self.index = (self.index + 1) % len(self.channels)
        return self.channels[self.index]
