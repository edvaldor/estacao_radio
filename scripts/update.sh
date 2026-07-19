#!/usr/bin/env bash
# Atualiza somente dependências declaradas; não troca major release do Python/OS.
set -euo pipefail
ROOT=/opt/radio-movel-sdr; LOG=/var/log/radio-movel-sdr-update.log; mode=${1:-}
[[ $EUID -eq 0 ]] || { echo 'Execute a atualização com sudo: sudo radioctl update'; exit 1; }
[[ -d $ROOT/.git ]] || { echo "Instalação em $ROOT não é um clone Git válido."; exit 1; }
check() { git -C "$ROOT" fetch --tags; echo "Instalado: $(cat "$ROOT/VERSION"); disponível: $(git -C "$ROOT" describe --tags --abbrev=0)"; }
[[ $mode == --check-only ]] && { check; exit 0; }
[[ $mode == --rollback ]] && { [[ -f "$ROOT/.previous-revision" ]] || { echo 'Não há versão anterior.'; exit 1; }; git -C "$ROOT" reset --hard "$(cat "$ROOT/.previous-revision")"; systemctl restart radio-movel-sdr; echo 'Código anterior restaurado. Pacotes APT não são revertidos automaticamente.'; exit 0; }
version=stable; [[ $mode == --version ]] && { [[ -n ${2:-} ]] || { echo 'Uso: update.sh --version TAG'; exit 2; }; version=$2; }
exec >>"$LOG" 2>&1; echo "$(date -Is) atualização solicitada: $version"
"$ROOT/scripts/backup.sh" "/var/backups/radio-movel-sdr/pre-update-$(date +%s).tar.gz"
old=$(git -C "$ROOT" rev-parse HEAD); echo "$old" >"$ROOT/.previous-revision"
trap 'git -C "$ROOT" reset --hard "$old"; echo "Atualização de código revertida"' ERR
git -C "$ROOT" fetch --tags; [[ $version == stable ]] && version=$(git -C "$ROOT" describe --tags --abbrev=0); git -C "$ROOT" checkout "$version"
"$ROOT/scripts/python-dependencies.sh"
[[ -x $ROOT/venv/bin/python ]] || python3 -m venv --system-site-packages "$ROOT/venv"
"$ROOT/venv/bin/python" -m compileall -q "$ROOT/app"
systemctl restart radio-movel-sdr; trap - ERR; echo 'Atualização concluída: código e componentes necessários foram validados.'
