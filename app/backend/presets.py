"""Durable user radio presets, kept independent from the Qt interface."""
import json
from pathlib import Path


class PresetStore:
    def __init__(self, path):
        self.path = Path(path)

    def load(self):
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        if not isinstance(data, list):
            return []
        return [item for item in data if self._valid(item)]

    def save(self, presets):
        clean = [dict(item) for item in presets if self._valid(item)]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(clean, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.path)

    def add(self, preset):
        presets = self.load()
        if not self._valid(preset):
            raise ValueError("Favorito inválido")
        presets.append(dict(preset))
        self.save(presets)
        return presets

    def remove(self, index):
        presets = self.load()
        del presets[index]
        self.save(presets)
        return presets

    @staticmethod
    def _valid(item):
        return (isinstance(item, dict) and isinstance(item.get("name"), str)
                and item["name"].strip() and isinstance(item.get("frequency_hz"), int)
                and not isinstance(item["frequency_hz"], bool) and item["frequency_hz"] > 0
                and item.get("modulation") in {"am", "fm", "nfm", "wfm"})
