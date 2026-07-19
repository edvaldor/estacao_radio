"""Validated radio settings; all frequencies are integer Hertz."""
from dataclasses import dataclass
from typing import Union

MODULATIONS = {"am", "fm", "wfm"}
RANGES = {"am": (24_000_000, 1_760_000_000), "fm": (24_000_000, 1_760_000_000), "wfm": (64_000_000, 108_000_000)}


def validate_frequency(value: int, modulation: str) -> int:
    if modulation not in MODULATIONS:
        raise ValueError("Modulação inválida. Use AM, FM ou WFM.")
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("A frequência deve ser um número inteiro em Hz.")
    low, high = RANGES[modulation]
    if not low <= value <= high:
        raise ValueError(f"Frequência fora da faixa suportada para {modulation.upper()}.")
    return value


def validate_gain(value: Union[str, int, float]) -> Union[str, float]:
    if value == "auto": return value
    if isinstance(value, bool): raise ValueError("Ganho inválido.")
    value = float(value)
    if not 0 <= value <= 49.6: raise ValueError("Ganho deve estar entre 0 e 49,6 dB ou automático.")
    return value


def validate_squelch(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 100:
        raise ValueError("Squelch deve estar entre 0 e 100.")
    return value

@dataclass(frozen=True)
class TuneRequest:
    frequency_hz: int
    modulation: str
    gain: Union[str, float] = "auto"
    squelch: int = 0
    sample_rate: int = 24000

    def __post_init__(self):
        validate_frequency(self.frequency_hz, self.modulation)
        validate_gain(self.gain); validate_squelch(self.squelch)
        if self.sample_rate not in {12000, 24000, 32000, 48000}:
            raise ValueError("Taxa de amostragem inválida.")
