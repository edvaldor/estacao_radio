#!/usr/bin/env bash
set -euo pipefail
ROOT=/opt/radio-movel-sdr; LOG=/var/log/radio-movel-sdr-update.log; mode=${1:-}
[[ $EUID -eq 0 ]] || { echo 'Execute com sudo: sudo radioctl update'; exit 1; }
[[ -d $ROOT/.git ]] || { echo "Instalação sem Git em $ROOT; execute o instalador para migrar."; exit 1; }
user=${SUDO_USER:-pi}; home=$(getent passwd "$user" | cut -d: -f6); : "${home:=/home/$user}"
check(){ git -C "$ROOT" fetch --tags; echo "Instalado: $(cat "$ROOT/VERSION"); disponível: $(git -C "$ROOT" tag --sort=-v:refname | head -n1)"; }
install_launcher(){ install -d -o "$user" -g "$user" -m 755 "$home/Desktop"; cat >"$home/Desktop/radio-movel-sdr.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Terminal=false
Name=Rádio Móvel SDR
Exec=/opt/radio-movel-sdr/scripts/launch-desktop.sh
Icon=applications-multimedia
EOF
chown "$user:$user" "$home/Desktop/radio-movel-sdr.desktop"; chmod 755 "$home/Desktop/radio-movel-sdr.desktop"; }
validate(){ "$ROOT/venv/bin/python" -m compileall -q "$ROOT/app"; }
[[ $mode == --check-only ]] && { check; exit 0; }
exec >>"$LOG" 2>&1; echo "$(date -Is) atualização solicitada: ${mode:-stable}"
backup=/var/backups/radio-movel-sdr/update-$(date +%Y%m%d-%H%M%S); mkdir -p "$backup"; "$ROOT/scripts/backup.sh" "$backup/settings.tar.gz"
old=$(git -C "$ROOT" rev-parse HEAD)
rollback(){ echo "$(date -Is) rollback: falha na validação"; git -C "$ROOT" reset --hard "$old"; }
trap rollback ERR
version=stable; [[ $mode == --version ]] && version=${2:?Uso: update.sh --version TAG}; git -C "$ROOT" fetch --tags; [[ $version == stable ]] && version=$(git -C "$ROOT" tag --sort=-v:refname | head -n1); [[ -n $version ]] || { echo 'Nenhuma tag estável.'; exit 1; }; git -C "$ROOT" checkout --detach "$version"
"$ROOT/scripts/python-dependencies.sh"; install_launcher; validate
trap - ERR; echo 'Atualização concluída. Abra a aplicação com duplo clique no lançador da área de trabalho.'
