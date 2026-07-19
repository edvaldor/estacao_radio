#!/usr/bin/env bash
# Validate the install copy-and-service step for both a clean install and a reinstall.
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
INSTALLER="$ROOT/scripts/install.sh"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

# The installer must copy the staged worktree before it renders the system unit,
# and must not install files onto their own existing paths.
copy_line=$(rg -n -F 'cp -a "$stage/source/." /opt/radio-movel-sdr/' "$INSTALLER" | cut -d: -f1)
service_line=$(rg -n -F 'sed "s/__USER__/$user/g" /opt/radio-movel-sdr/systemd/radio-movel-sdr.service > /etc/systemd/system/radio-movel-sdr.service' "$INSTALLER" | cut -d: -f1)
reload_line=$(rg -n -F '  systemctl daemon-reload' "$INSTALLER" | cut -d: -f1)
enable_line=$(rg -n -F '  systemctl enable --now radio-movel-sdr.service' "$INSTALLER" | cut -d: -f1)
[[ $copy_line =~ ^[0-9]+$ && $service_line =~ ^[0-9]+$ ]]
[[ $reload_line =~ ^[0-9]+$ && $enable_line =~ ^[0-9]+$ ]]
[[ $copy_line -lt $service_line && $service_line -lt $reload_line && $reload_line -lt $enable_line ]]
if rg -F 'install -m 755 /opt/radio-movel-sdr/scripts/start-graphical-session.sh' "$INSTALLER"; then
  echo 'O instalador não deve copiar scripts já presentes no destino.' >&2
  exit 1
fi

install_and_verify() {
  local destination=$1 user=$2
  cp -a "$ROOT/." "$destination/"
  sed "s/__USER__/$user/g" "$destination/systemd/radio-movel-sdr.service" >"$work/radio-movel-sdr.service"
  test -s "$work/radio-movel-sdr.service"
  rg -F "User=$user" "$work/radio-movel-sdr.service" >/dev/null
}

mkdir -p "$work/installed"
install_and_verify "$work/installed" pi
install_and_verify "$work/installed" radio
