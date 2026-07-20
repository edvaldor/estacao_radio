#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.."; && pwd); DRY=0; NON=0
for arg in "$@"; do case "$arg" in --dry-run) DRY=1;; --non-interactive) NON=1;; *) echo "Opção inválida: $arg"; exit 2;; esac; done
run(){ if ((DRY)); then printf '[simulação]'; printf ' %q' "$@"; echo; else "$@"; fi; }
[[ $EUID -eq 0 ]] || { echo 'Execute com sudo.'; exit 1; }
model=''; if [[ -r /proc/device-tree/model ]]; then model=$(tr -d '\0' </proc/device-tree/model); fi; arch=$(uname -m); os=$(grep '^ID=' /etc/os-release|cut -d= -f2)
echo "Modelo: ${model:-não identificado}; arquitetura: $arch; sistema: $os"
[[ "$model" == *Raspberry*Pi* && "$arch" == armv7l && "$os" == raspbian ]] || { echo 'Sistema incompatível: requer Raspberry Pi OS Lite 32-bit ARMv7 em Raspberry Pi.'; exit 1; }
[[ $(df -Pm /opt|awk 'NR==2{print $4}') -ge 900 ]] || { echo 'Espaço insuficiente: são necessários 900 MB livres.'; exit 1; }
ping -c1 -W3 deb.debian.org >/dev/null || { echo 'Sem internet; conecte a rede para instalar dependências.'; exit 1; }
user=${SUDO_USER:-$(loginctl list-users --no-legend 2>/dev/null|awk 'NR==1{print $2}')}; : "${user:=pi}"
home=$(getent passwd "$user" | cut -d: -f6); : "${home:=/home/$user}"
echo "Usuário da interface: $user"; echo 'Saídas ALSA encontradas:'; aplay -l 2>/dev/null || true
if (( ! NON )); then read -r -p 'Dispositivo ALSA [default]: ' audio; else audio=default; fi; : "${audio:=default}"
backup=/var/backups/radio-movel-sdr/$(date +%Y%m%d-%H%M%S); run mkdir -p "$backup" /var/lib/radio-movel-sdr
[[ -e /etc/systemd/system/radio-movel-sdr.service ]] && run cp -a /etc/systemd/system/radio-movel-sdr.service "$backup/"
run "$ROOT/scripts/python-dependencies.sh"
run install -d -m 755 /opt/radio-movel-sdr
# Keep a real Git worktree in the installed location: update.sh relies on it.
# A local source is intentional fallback for offline/test repositories without origin.
source_url=$(git -C "$ROOT" remote get-url origin 2>/dev/null || printf '%s' "$ROOT")
revision=$(git -C "$ROOT" rev-parse HEAD 2>/dev/null || true)
[[ -n $revision ]] || { echo 'A origem da instalação deve ser um repositório Git válido.'; exit 1; }
stage=$(mktemp -d); trap 'rm -rf "$stage"' EXIT
if ((DRY)); then
  echo "[simulação] git clone --no-checkout $source_url $stage/source; git checkout --detach $revision"
else
  git clone --no-checkout "$source_url" "$stage/source"
  git -C "$stage/source" checkout --detach "$revision"
  # Deliberately do not delete venv or user data; copy the complete worktree,
  # including .git, so official installs can subsequently update.
  cp -a "$stage/source/." /opt/radio-movel-sdr/
fi
[[ -d /opt/radio-movel-sdr/venv ]] || run python3 -m venv --system-site-packages /opt/radio-movel-sdr/venv
[[ -e /var/lib/radio-movel-sdr/settings.json ]] || run cp "$ROOT/config/settings.example.json" /var/lib/radio-movel-sdr/settings.json
[[ -e /var/lib/radio-movel-sdr/presets.json ]] || run cp "$ROOT/config/presets.example.json" /var/lib/radio-movel-sdr/presets.json
if (( ! DRY )); then /opt/radio-movel-sdr/venv/bin/python - "$audio" <<'PY'
import json,sys
p='/var/lib/radio-movel-sdr/settings.json'; d=json.load(open(p)); d['audio_device']=sys.argv[1]; open(p,'w').write(json.dumps(d,indent=2)+'\n')
PY
fi
run install -m 755 /opt/radio-movel-sdr/radioctl /usr/local/bin/radioctl
# Remove the retired service: the user's existing graphical session owns Xorg.
if (( ! DRY )); then
  usermod -aG video,render,input,audio,gpio "$user" 2>/dev/null || usermod -aG video,render,input,audio "$user"
  systemctl disable --now radio-movel-sdr.service 2>/dev/null || true
  rm -f /etc/systemd/system/radio-movel-sdr.service
  systemctl daemon-reload
  install -d -o "$user" -g "$user" -m 755 "$home/Desktop"
  cat >"$home/Desktop/radio-movel-sdr.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Terminal=false
Name=Rádio Móvel SDR
Exec=/opt/radio-movel-sdr/scripts/launch-desktop.sh
Icon=applications-multimedia
EOF
  chown "$user:$user" "$home/Desktop/radio-movel-sdr.desktop"
  chmod 755 "$home/Desktop/radio-movel-sdr.desktop"
else
  echo "[simulação] desabilitar serviço antigo e criar $home/Desktop/radio-movel-sdr.desktop"
fi
echo "Instalação concluída. Na sessão gráfica de $user, abra Rádio Móvel SDR com duplo clique em $home/Desktop/radio-movel-sdr.desktop. Diagnóstico: radioctl doctor."
