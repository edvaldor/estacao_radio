import tempfile
import unittest
import wave
from pathlib import Path

from app.backend.recording import WavRecorder


class RecordingTest(unittest.TestCase):
    def test_wav_lifecycle_writes_pcm_and_closes_file(self):
        with tempfile.TemporaryDirectory() as directory:
            recorder = WavRecorder(directory, sample_rate=8_000)
            path = recorder.start(118_000_000)
            recorder.write(b"\x00\x00" * 40)
            recorder.stop()
            self.assertFalse(recorder.active)
            with wave.open(str(path), "rb") as saved:
                self.assertEqual(saved.getframerate(), 8_000)
                self.assertEqual(saved.getnframes(), 40)

    def test_stop_is_safe_when_not_recording(self):
        with tempfile.TemporaryDirectory() as directory:
            WavRecorder(Path(directory)).stop()
