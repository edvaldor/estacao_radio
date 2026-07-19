#!/usr/bin/env bash
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo 'Execute com sudo.'; exit 1; }
systemctl disable --now radio-movel-sdr.service 2>/dev/null || true
rm -f /etc/systemd/system/radio-movel-sdr.service /usr/local/bin/radioctl
systemctl daemon-reload
rm -rf /opt/radio-movel-sdr
echo 'Aplicação removida; configurações em /var/lib/radio-movel-sdr foram preservadas.'
