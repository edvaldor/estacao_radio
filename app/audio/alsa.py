"""Small ALSA mixer adapter; failures are reported to the UI without a shell."""
import shutil
import subprocess


def set_volume(percent):
    if isinstance(percent, bool) or not isinstance(percent, int) or not 0 <= percent <= 100:
        raise ValueError("Volume deve estar entre 0 e 100%.")
    if not shutil.which("amixer"):
        raise RuntimeError("amixer não encontrado; não foi possível ajustar o volume.")
    completed = subprocess.run(["amixer", "-q", "sset", "Master", f"{percent}%"], capture_output=True, text=True)
    if completed.returncode:
        message = completed.stderr.strip() or "controle ALSA Master indisponível"
        raise RuntimeError(f"Não foi possível ajustar o volume: {message}")
