#!/usr/bin/env bash
set -euo pipefail
[[ $# -eq 1 && -f $1 ]] || { echo 'Uso: restore.sh ARQUIVO.tar.gz'; exit 2; }; systemctl stop radio-movel-sdr.service 2>/dev/null || true; tar -C /var/lib -xzf "$1"; systemctl start radio-movel-sdr.service 2>/dev/null || true; echo 'Configurações restauradas.'
