#!/usr/bin/env bash
set -euo pipefail
ROOT=/opt/radio-movel-sdr; LOG=/var/log/radio-movel-sdr-update.log; SERVICE=radio-movel-sdr.service; mode=${1:-}
[[ $EUID -eq 0 ]] || { echo 'Execute com sudo: sudo radioctl update'; exit 1; }
[[ -d $ROOT/.git ]] || { echo "Instalação sem Git em $ROOT; execute o instalador para migrar."; exit 1; }
user=${SUDO_USER:-pi}; SERVICE_FILE=/etc/systemd/system/$SERVICE
check(){ git -C "$ROOT" fetch --tags; echo "Instalado: $(cat "$ROOT/VERSION"); disponível: $(git -C "$ROOT" tag --sort=-v:refname | head -n1)"; }
sync_service(){ /bin/bash "$ROOT/scripts/migrate-x-startup.sh" "$user" "$backup"; usermod -aG video,render,input,audio,gpio "$user" 2>/dev/null || true; sed "s/__USER__/$user/g" "$ROOT/systemd/$SERVICE" >"$SERVICE_FILE"; chmod 644 "$SERVICE_FILE"; systemctl disable --now radio-movel-sdr-user.service 2>/dev/null || true; rm -f "/home/$user/.config/systemd/user/radio-movel-sdr-user.service"; systemctl daemon-reload; systemd-analyze verify "$SERVICE_FILE"; systemctl enable "$SERVICE"; }
validate(){ systemctl restart "$SERVICE"; sleep 4; systemctl is-active --quiet "$SERVICE" && pgrep -u "$user" -x Xorg >/dev/null && pgrep -u "$user" -f 'python.*app.main' >/dev/null; }
[[ $mode == --check-only ]] && { check; exit 0; }
exec >>"$LOG" 2>&1; echo "$(date -Is) atualização solicitada: ${mode:-stable}"
backup=/var/backups/radio-movel-sdr/update-$(date +%Y%m%d-%H%M%S); mkdir -p "$backup"; "$ROOT/scripts/backup.sh" "$backup/settings.tar.gz"
old=$(git -C "$ROOT" rev-parse HEAD); cp -a "$SERVICE_FILE" "$backup/" 2>/dev/null || true
rollback(){ echo "$(date -Is) rollback: serviço não permaneceu aberto"; git -C "$ROOT" reset --hard "$old"; [[ -f "$backup/$SERVICE" ]] && cp -a "$backup/$SERVICE" "$SERVICE_FILE"; systemctl daemon-reload; systemctl restart "$SERVICE" || true; }
trap rollback ERR
version=stable; [[ $mode == --version ]] && version=${2:?Uso: update.sh --version TAG}; git -C "$ROOT" fetch --tags; [[ $version == stable ]] && version=$(git -C "$ROOT" tag --sort=-v:refname | head -n1); [[ -n $version ]] || { echo 'Nenhuma tag estável.'; exit 1; }; git -C "$ROOT" checkout --detach "$version"
"$ROOT/scripts/python-dependencies.sh"; "$ROOT/venv/bin/python" -m compileall -q "$ROOT/app"; sync_service; validate
trap - ERR; echo 'Atualização concluída e X/interface permaneceram ativos.'
