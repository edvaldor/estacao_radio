#!/usr/bin/env bash
set -euo pipefail
out=${1:-"$PWD/radio-movel-sdr-backup-$(date +%Y%m%d-%H%M%S).tar.gz"}; tar -C /var/lib -czf "$out" radio-movel-sdr; echo "Backup criado: $out"
