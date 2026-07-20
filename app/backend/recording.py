"""WAV recorder that accepts PCM blocks from a receiver pump thread."""
import shutil
import threading
import time
import wave
from pathlib import Path


class WavRecorder:
    def __init__(self, directory, sample_rate=24_000):
        self.directory, self.sample_rate = Path(directory), sample_rate
        self._wave = None
        self._lock = threading.Lock()
        self.path = None

    @property
    def active(self):
        return self._wave is not None

    def start(self, frequency_hz):
        self.stop()
        self.directory.mkdir(parents=True, exist_ok=True)
        if shutil.disk_usage(self.directory).free < 1024 * 1024:
            raise RuntimeError("Espaço insuficiente para gravação")
        stamp = time.strftime("%Y%m%d-%H%M%S") + f"-{time.time_ns() % 1_000_000_000:09d}"
        self.path = self.directory / f"radio-{int(frequency_hz)}Hz-{stamp}.wav"
        self._wave = wave.open(str(self.path), "wb")
        self._wave.setnchannels(1); self._wave.setsampwidth(2); self._wave.setframerate(self.sample_rate)
        return self.path

    def write(self, data):
        with self._lock:
            if self._wave:
                self._wave.writeframesraw(data)

    def stop(self):
        with self._lock:
            if self._wave:
                self._wave.close()
                self._wave = None
