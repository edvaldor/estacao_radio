#!/usr/bin/env bash
# Started by the desktop entry, never by systemd: it uses the current X11 session.
set -Eeuo pipefail

ROOT=/opt/radio-movel-sdr
STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/radio-movel-sdr"
LOG="$STATE_DIR/launch.log"
LOCK="$STATE_DIR/launch.lock"

mkdir -p "$STATE_DIR"
exec >>"$LOG" 2>&1
echo "$(date -Is) launcher invoked (DISPLAY=${DISPLAY:-unset})"

if [[ -z ${DISPLAY:-} ]]; then
  echo "$(date -Is) erro: este lançador deve ser aberto dentro de uma sessão gráfica."
  exit 1
fi

export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-xcb}"

exec 9>"$LOCK"
if ! flock -n 9; then
  echo "$(date -Is) uma instância já está em execução; lançamento ignorado."
  exit 0
fi

cd "$ROOT"
echo "$(date -Is) iniciando aplicação"
"$ROOT/venv/bin/python" -m app.main
status=$?
echo "$(date -Is) aplicação encerrada com status $status"
exit "$status"
