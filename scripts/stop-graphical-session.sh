#!/usr/bin/env bash
set -euo pipefail
# KillMode=control-group also terminates rtl_fm, aplay and Xorg.
pkill -TERM -u "${USER:-pi}" -f '/opt/radio-movel-sdr/venv/bin/python -m app.main' 2>/dev/null || true
