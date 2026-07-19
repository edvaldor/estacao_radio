#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd); DRY=0; NON=0
for arg in "$@"; do case "$arg" in --dry-run) DRY=1;; --non-interactive) NON=1;; *) echo "Opção inválida: $arg"; exit 2;; esac; done
run(){ if ((DRY)); then printf '[simulação]'; printf ' %q' "$@"; echo; else "$@"; fi; }
[[ $EUID -eq 0 ]] || { echo 'Execute com sudo.'; exit 1; }
model=''; if [[ -r /proc/device-tree/model ]]; then model=$(tr -d '\0' </proc/device-tree/model); fi; arch=$(uname -m); os=$(grep '^ID=' /etc/os-release|cut -d= -f2)
echo "Modelo: ${model:-não identificado}; arquitetura: $arch; sistema: $os"
[[ "$model" == *Raspberry*Pi* && "$arch" == armv7l && "$os" == raspbian ]] || { echo 'Sistema incompatível: requer Raspberry Pi OS Lite 32-bit ARMv7 em Raspberry Pi.'; exit 1; }
[[ $(df -Pm /opt|awk 'NR==2{print $4}') -ge 900 ]] || { echo 'Espaço insuficiente: são necessários 900 MB livres.'; exit 1; }
ping -c1 -W3 deb.debian.org >/dev/null || { echo 'Sem internet; conecte a rede para instalar dependências.'; exit 1; }
user=${SUDO_USER:-$(loginctl list-users --no-legend 2>/dev/null|awk 'NR==1{print $2}')}; : "${user:=pi}"
echo "Usuário da interface: $user"; echo 'Saídas ALSA encontradas:'; aplay -l 2>/dev/null || true
if (( ! NON )); then read -r -p 'Dispositivo ALSA [default]: ' audio; else audio=default; fi; : "${audio:=default}"
backup=/var/backups/radio-movel-sdr/$(date +%Y%m%d-%H%M%S); run mkdir -p "$backup" /var/lib/radio-movel-sdr
[[ -e /etc/systemd/system/radio-movel-sdr.service ]] && run cp -a /etc/systemd/system/radio-movel-sdr.service "$backup/"
run "$ROOT/scripts/python-dependencies.sh"
run install -d -m 755 /opt/radio-movel-sdr; [[ -d /opt/radio-movel-sdr/venv ]] || run python3 -m venv --system-site-packages /opt/radio-movel-sdr/venv; run cp -a "$ROOT/app" "$ROOT/config" "$ROOT/scripts" "$ROOT/radioctl" "$ROOT/VERSION" /opt/radio-movel-sdr/
[[ -e /var/lib/radio-movel-sdr/settings.json ]] || run cp "$ROOT/config/settings.example.json" /var/lib/radio-movel-sdr/settings.json
[[ -e /var/lib/radio-movel-sdr/presets.json ]] || run cp "$ROOT/config/presets.example.json" /var/lib/radio-movel-sdr/presets.json
if (( ! DRY )); then /opt/radio-movel-sdr/venv/bin/python - "$audio" <<'PY'
import json,sys
p='/var/lib/radio-movel-sdr/settings.json'; d=json.load(open(p)); d['audio_device']=sys.argv[1]; open(p,'w').write(json.dumps(d,indent=2)+'\n')
PY
fi
if ((DRY)); then echo "[simulação] criar serviço systemd para $user"; else sed "s/__USER__/$user/g" "$ROOT/systemd/radio-movel-sdr.service" > /etc/systemd/system/radio-movel-sdr.service; chmod 644 /etc/systemd/system/radio-movel-sdr.service; fi; run install -m 755 "$ROOT/radioctl" /usr/local/bin/radioctl; run systemctl daemon-reload; run systemctl enable radio-movel-sdr.service
echo 'Instalação concluída. Reinicie com: sudo reboot. Diagnóstico: radioctl doctor.'
