#!/usr/bin/env bash
set -euo pipefail
purge=0; [[ ${1:-} == --purge-data ]] && purge=1
user=${SUDO_USER:-pi}; uid=$(id -u "$user"); user_systemctl(){ runuser -u "$user" -- env XDG_RUNTIME_DIR="/run/user/$uid" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$uid/bus" systemctl --user "$@"; }
user_systemctl disable --now radio-movel-sdr-user.service 2>/dev/null || true; rm -f "/home/$user/.config/systemd/user/radio-movel-sdr-user.service" /usr/local/bin/radioctl
systemctl disable --now radio-movel-sdr.service 2>/dev/null || true; rm -f /etc/systemd/system/radio-movel-sdr.service; user_systemctl daemon-reload 2>/dev/null || true; systemctl daemon-reload; rm -rf /opt/radio-movel-sdr
if ((purge)); then rm -rf /var/lib/radio-movel-sdr; echo 'Aplicativo e dados removidos.'; else echo 'Aplicativo removido; favoritos e configurações foram preservados em /var/lib/radio-movel-sdr.'; fi
