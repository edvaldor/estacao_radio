#!/usr/bin/env bash
# Atualiza somente dependências declaradas; não troca major release do Python/OS.
set -euo pipefail
ROOT=/opt/radio-movel-sdr; LOG=/var/log/radio-movel-sdr-update.log; SERVICE=radio-movel-sdr.service; SERVICE_FILE=/etc/systemd/system/radio-movel-sdr.service; mode=${1:-}
[[ $EUID -eq 0 ]] || { echo 'Execute a atualização com sudo: sudo radioctl update'; exit 1; }
[[ -d $ROOT/.git ]] || { echo "Instalação em $ROOT não possui metadados Git. Reinstale com scripts/install.sh para migrar instalações antigas."; exit 1; }
check() { git -C "$ROOT" fetch --tags; echo "Instalado: $(cat "$ROOT/VERSION"); disponível: $(git -C "$ROOT" tag --sort=-v:refname | head -n1)"; }
sync_service() {
  local user
  user=$(systemctl show --property=User --value "$SERVICE" 2>/dev/null || true)
  : "${user:=${SUDO_USER:-pi}}"
  sed "s/__USER__/$user/g" "$ROOT/systemd/$SERVICE" >"$SERVICE_FILE"
  chmod 644 "$SERVICE_FILE"
  systemctl daemon-reload
  systemctl enable "$SERVICE"
}
[[ $mode == --check-only ]] && { check; exit 0; }
[[ $mode == --rollback ]] && { [[ -f "$ROOT/.previous-revision" ]] || { echo 'Não há versão anterior.'; exit 1; }; git -C "$ROOT" reset --hard "$(cat "$ROOT/.previous-revision")"; sync_service; systemctl restart "$SERVICE"; echo 'Código anterior restaurado. Pacotes APT não são revertidos automaticamente.'; exit 0; }
version=stable; [[ $mode == --version ]] && { [[ -n ${2:-} ]] || { echo 'Uso: update.sh --version TAG'; exit 2; }; version=$2; }
exec >>"$LOG" 2>&1; echo "$(date -Is) atualização solicitada: $version"
"$ROOT/scripts/backup.sh" "/var/backups/radio-movel-sdr/pre-update-$(date +%s).tar.gz"
old=$(git -C "$ROOT" rev-parse HEAD); echo "$old" >"$ROOT/.previous-revision"
service_backup=$(mktemp); cp -a "$SERVICE_FILE" "$service_backup"
rollback() {
  git -C "$ROOT" reset --hard "$old"
  cp -a "$service_backup" "$SERVICE_FILE"
  systemctl daemon-reload
  systemctl restart "$SERVICE" || true
  echo 'Atualização de código e serviço revertida'
}
trap rollback ERR
git -C "$ROOT" fetch --tags; [[ $version == stable ]] && version=$(git -C "$ROOT" tag --sort=-v:refname | head -n1); [[ -n $version ]] || { echo 'Nenhuma tag estável foi encontrada no repositório remoto.'; exit 1; }; git -C "$ROOT" checkout --detach "$version"
"$ROOT/scripts/python-dependencies.sh"
[[ -x $ROOT/venv/bin/python ]] || python3 -m venv --system-site-packages "$ROOT/venv"
"$ROOT/venv/bin/python" -m compileall -q "$ROOT/app"
sync_service
systemctl restart "$SERVICE"
systemctl is-active --quiet "$SERVICE"
rm -f "$service_backup"
trap - ERR
echo 'Atualização concluída: código, serviço e componentes necessários foram validados.'
