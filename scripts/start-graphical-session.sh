#!/usr/bin/env bash
# The only supported owner of X for this appliance. Do not put startx in a profile.
set -euo pipefail
cd /opt/radio-movel-sdr
display=${DISPLAY:-:0}
lock=/tmp/.X${display#:}-lock
if [[ -e $lock ]]; then
  pid=$(cat "$lock" 2>/dev/null || true)
  if [[ $pid =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null; then
    echo "X $display já pertence ao processo $pid; recusando disputar o display" >&2
    exit 1
  fi
  echo "Removendo lock X abandonado: $lock" >&2
  rm -f "$lock"
fi
exec /usr/bin/xinit /opt/radio-movel-sdr/venv/bin/python -m app.main -- :0 vt1 -keeptty -nolisten tcp
