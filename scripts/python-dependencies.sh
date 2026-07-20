#!/usr/bin/env bash
# Pacotes do sistema, deliberadamente sem pip: PyQt5/gpiozero precisam acompanhar o Raspberry Pi OS.
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo 'Execute com sudo para instalar componentes Python.'; exit 1; }
apt-get update
apt-get install -y --no-install-recommends \
  python3 python3-venv python3-pyqt5 python3-gpiozero \
  rtl-sdr alsa-utils xserver-xorg xserver-xorg-input-libinput xinit x11-xserver-utils xinput xinput-calibrator
