#!/usr/bin/env bash
set -euo pipefail
[[ $# -eq 1 && -f $1 ]] || { echo 'Uso: restore.sh ARQUIVO.tar.gz'; exit 2; }
archive=$1; work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
# Accept only regular settings/presets files rooted at the application's backup path.
mapfile -t members < <(tar -tzf "$archive")
[[ ${#members[@]} -gt 0 ]] || { echo 'Backup vazio ou inválido.'; exit 1; }
for member in "${members[@]}"; do
  [[ $member == radio-movel-sdr/settings.json || $member == radio-movel-sdr/presets.json ]] || { echo "Backup recusado: contém caminho não permitido: $member"; exit 1; }
done
while IFS= read -r entry; do
  [[ ${entry:0:1} == - ]] || { echo 'Backup recusado: contém entrada não regular.'; exit 1; }
done < <(tar -tvzf "$archive")
tar -xzf "$archive" -C "$work" --no-same-owner --no-same-permissions
for file in settings.json presets.json; do
  [[ -f $work/radio-movel-sdr/$file && ! -L $work/radio-movel-sdr/$file ]] || { echo "Backup recusado: $file não é arquivo regular."; exit 1; }
done
user=${SUDO_USER:-pi}; uid=$(id -u "$user"); user_systemctl(){ runuser -u "$user" -- env XDG_RUNTIME_DIR="/run/user/$uid" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$uid/bus" systemctl --user "$@"; }
user_systemctl stop radio-movel-sdr-user.service 2>/dev/null || true
install -d -m 755 /var/lib/radio-movel-sdr
install -m 600 "$work/radio-movel-sdr/settings.json" /var/lib/radio-movel-sdr/settings.json
install -m 600 "$work/radio-movel-sdr/presets.json" /var/lib/radio-movel-sdr/presets.json
user_systemctl start radio-movel-sdr-user.service 2>/dev/null || true
echo 'Configurações restauradas com segurança.'
