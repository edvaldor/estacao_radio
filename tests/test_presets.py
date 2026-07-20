import tempfile
import unittest
from pathlib import Path

from app.backend.presets import PresetStore


class PresetStoreTest(unittest.TestCase):
    def test_add_remove_and_reload_preset(self):
        with tempfile.TemporaryDirectory() as directory:
            store = PresetStore(Path(directory) / "presets.json")
            store.add({"name": "Torre", "frequency_hz": 118_000_000, "modulation": "am"})
            self.assertEqual(store.load()[0]["name"], "Torre")
            store.remove(0)
            self.assertEqual(store.load(), [])

    def test_invalid_file_does_not_break_ui(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "presets.json"; path.write_text("not json")
            self.assertEqual(PresetStore(path).load(), [])
