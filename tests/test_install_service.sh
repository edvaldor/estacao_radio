#!/usr/bin/env bash
# Validate the install copy and display-configuration integration.
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
INSTALLER="$ROOT/scripts/install.sh"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

# Display setup must run from the source tree, before the staged worktree is copied.
copy_line=$(rg -n -F 'cp -a "$stage/source/." /opt/radio-movel-sdr/' "$INSTALLER" | cut -d: -f1)
display_line=$(rg -n -F 'run "$ROOT/scripts/configure-display.sh" "${display_args[@]}"' "$INSTALLER" | cut -d: -f1)
[[ $copy_line =~ ^[0-9]+$ && $display_line =~ ^[0-9]+$ ]]
[[ $display_line -lt $copy_line ]]

DISPLAY_CONFIG="$ROOT/scripts/configure-display.sh"
bash -n "$INSTALLER" "$DISPLAY_CONFIG"
rg -F 'dtparam=spi=on' "$DISPLAY_CONFIG" >/dev/null
rg -F 'dtoverlay=waveshare32b:rotate=90' "$DISPLAY_CONFIG" >/dev/null
rg -F 'framebuffer_width=320' "$DISPLAY_CONFIG" >/dev/null
rg -F '/boot/firmware/config.txt /boot/config.txt' "$DISPLAY_CONFIG" >/dev/null
rg -F 'https://github.com/waveshareteam/LCD-show.git' "$DISPLAY_CONFIG" >/dev/null
rg -F 'waveshare32b-overlay.dtb' "$DISPLAY_CONFIG" >/dev/null
rg -F 'xinput_calibrator' "$DISPLAY_CONFIG" >/dev/null

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
