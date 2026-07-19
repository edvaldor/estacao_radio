import json
from pathlib import Path

class SettingsStore:
    def __init__(self, path): self.path = Path(path)
    def load(self, defaults):
        try:
            with self.path.open(encoding="utf-8") as f: saved = json.load(f)
            return {**defaults, **saved}
        except (OSError, json.JSONDecodeError): return dict(defaults)
    def save(self, values):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(values, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        temporary.replace(self.path)
