#!/usr/bin/env bash
set -euo pipefail
purge=0; [[ ${1:-} == --purge-data ]] && purge=1
systemctl disable --now radio-movel-sdr.service 2>/dev/null || true; rm -f /etc/systemd/system/radio-movel-sdr.service /usr/local/bin/radioctl; systemctl daemon-reload; rm -rf /opt/radio-movel-sdr
if ((purge)); then rm -rf /var/lib/radio-movel-sdr; echo 'Aplicativo e dados removidos.'; else echo 'Aplicativo removido; favoritos e configurações foram preservados em /var/lib/radio-movel-sdr.'; fi
