#!/usr/bin/env bash
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo 'Execute com sudo.'; exit 1; }
systemctl disable --now radio-movel-sdr.service 2>/dev/null || true
rm -f /etc/systemd/system/radio-movel-sdr.service /usr/local/bin/radioctl
systemctl daemon-reload
user=${SUDO_USER:-pi}; home=$(getent passwd "$user" | cut -d: -f6); : "${home:=/home/$user}"
rm -f "$home/Desktop/radio-movel-sdr.desktop"
rm -rf /opt/radio-movel-sdr
echo 'Aplicação e lançador da área de trabalho removidos; configurações em /var/lib/radio-movel-sdr foram preservadas.'
