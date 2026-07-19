import json
import logging
from pathlib import Path
from .models import MODULATIONS, validate_frequency, validate_gain, validate_squelch

LOG = logging.getLogger(__name__)


def validated_settings(saved, defaults):
    """Return only valid persisted fields, falling back field-by-field safely."""
    if not isinstance(saved, dict):
        raise ValueError("a raiz do JSON deve ser um objeto")
    result = dict(defaults)
    validators = {
        "mode": lambda value: value if isinstance(value, str) and value else (_ for _ in ()).throw(ValueError()),
        "modulation": lambda value: value if isinstance(value, str) and value in MODULATIONS else (_ for _ in ()).throw(ValueError()),
        "step_hz": lambda value: value if isinstance(value, int) and not isinstance(value, bool) and 1 <= value <= 1_000_000 else (_ for _ in ()).throw(ValueError()),
        "gain": validate_gain, "squelch": validate_squelch,
        "volume": lambda value: value if isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 100 else (_ for _ in ()).throw(ValueError()),
        "audio_device": lambda value: value if isinstance(value, str) and value else (_ for _ in ()).throw(ValueError()),
        "rtl_serial": lambda value: value if value is None or isinstance(value, str) else (_ for _ in ()).throw(ValueError()),
        "demo_mode": lambda value: value if isinstance(value, bool) else (_ for _ in ()).throw(ValueError()),
        "scanner_dwell_seconds": lambda value: value if isinstance(value, int) and not isinstance(value, bool) and 1 <= value <= 3600 else (_ for _ in ()).throw(ValueError()),
    }
    # Modulation determines the valid frequency range, so process it first.
    keys = (["modulation"] if "modulation" in defaults else []) + [key for key in defaults if key != "modulation"]
    for key in keys:
        default = defaults[key]
        if key not in saved:
            continue
        try:
            value = validators.get(key, lambda item: item)(saved[key])
            if key == "frequency_hz" and "modulation" in result:
                # Validate against the persisted modulation, only after it was checked.
                value = validate_frequency(value, result["modulation"])
            result[key] = value
        except (TypeError, ValueError):
            LOG.warning("Configuração inválida para %s; usando valor padrão.", key)
            result[key] = default
    # A frequency valid for its old modulation may be invalid after a bad modulation.
    if "frequency_hz" in result and "modulation" in result:
        try:
            result["frequency_hz"] = validate_frequency(result["frequency_hz"], result["modulation"])
        except ValueError:
            LOG.warning("Frequência persistida inválida; usando valor padrão.")
            result["frequency_hz"] = defaults["frequency_hz"]
    return result

class SettingsStore:
    def __init__(self, path): self.path = Path(path)
    def load(self, defaults):
        try:
            with self.path.open(encoding="utf-8") as f: saved = json.load(f)
            return validated_settings(saved, defaults)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            LOG.warning("Não foi possível carregar configurações (%s); usando padrões.", exc)
            return dict(defaults)
    def save(self, values):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(values, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        temporary.replace(self.path)
