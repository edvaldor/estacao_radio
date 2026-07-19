#!/usr/bin/env bash
# Diagnóstico deliberadamente baseado no nome do dispositivo, não em eventN.
set -u

ui_user=${RADIO_UI_USER:-pi}
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
python_bin=${RADIO_PYTHON:-}
[[ -n $python_bin ]] || {
  if [[ -x /opt/radio-movel-sdr/venv/bin/python ]]; then python_bin=/opt/radio-movel-sdr/venv/bin/python
  else python_bin=python3; fi
}

config_file=''
for candidate in /boot/firmware/config.txt /boot/config.txt; do
  [[ -r $candidate ]] && { config_file=$candidate; break; }
done
config_has(){ [[ -n $config_file ]] && sed -E 's/[[:space:]]*#.*$//' "$config_file" | grep -Eq "$1"; }

echo '=== Diagnóstico Rádio Móvel SDR ==='
echo "Usuário da UI: $ui_user"
echo "Sistema: $(. /etc/os-release 2>/dev/null; echo "${PRETTY_NAME:-desconhecido}")"
echo "Kernel: $(uname -a)"
echo 'RTL-SDR:'
command -v rtl_test >/dev/null && timeout 15 rtl_test -t || echo 'rtl_test não disponível ou SDR não detectado.'

echo 'Tela/framebuffer:'
framebuffers=$(find /sys/class/graphics -maxdepth 1 -name 'fb*' -printf '%f\n' 2>/dev/null || true)
[[ -n $framebuffers ]] && printf '%s\n' "$framebuffers" || echo 'AUSENTE: nenhum framebuffer foi detectado.'

echo 'SPI:'
spi_devices=$(compgen -G '/dev/spidev*' || true)
[[ -n $spi_devices ]] && printf '%s\n' "$spi_devices" || echo 'AUSENTE: nenhum /dev/spidev*; habilite SPI e reinicie.'
if config_has '^[[:space:]]*dtparam=spi=on([[:space:]]|$)'; then
  echo "Configuração SPI: habilitada em $config_file"
else
  echo "AUSENTE: dtparam=spi=on não encontrado em ${config_file:-/boot/firmware/config.txt ou /boot/config.txt}."
fi

echo 'Overlay Waveshare:'
if config_has '^[[:space:]]*dtoverlay=waveshare32b([,[:space:]]|$)'; then
  echo "waveshare32b configurado em $config_file"
else
  echo "AUSENTE: dtoverlay=waveshare32b não encontrado em ${config_file:-config.txt}."
fi

echo 'Touchscreen (por nome, nunca event fixo):'
touch_found=0
for name_file in /sys/class/input/event*/device/name; do
  [[ -r $name_file ]] || continue
  name=$(<"$name_file")
  [[ $name =~ [Aa][Dd][Ss]7846|[Tt]ouchscreen ]] || continue
  event_name=$(basename "$(dirname "$(dirname "$name_file")")")
  event_device="/dev/input/$event_name"
  touch_found=1
  echo "$event_device: $name ($name_file)"
  if [[ -e $event_device ]] && "$python_bin" -c "import sys; sys.path.insert(0, sys.argv[1]); from app.diagnostics.system import user_can_read; raise SystemExit(not user_can_read(sys.argv[2], sys.argv[3]))" "$repo_root" "$event_device" "$ui_user"; then
    echo "  Permissão: $ui_user pode ler $event_device"
  else
    echo "  AUSENTE/NEGADO: $ui_user não pode ler $event_device; inclua-o no grupo proprietário (normalmente input) e faça novo login."
  fi
done
(( touch_found )) || echo 'AUSENTE: ADS7846/touchscreen não encontrado em /sys/class/input. Verifique SPI, o overlay waveshare32b e reinicie.'

echo 'Qt e entrada (modo selecionado: X11):'
echo 'QT_QPA_PLATFORM=xcb (definido em systemd/radio-movel-sdr-user.service); não configure QT_QPA_EVDEV_TOUCHSCREEN_PARAMETERS neste modo.'
if "$python_bin" -c "import sys; sys.path.insert(0, sys.argv[1]); from app.diagnostics.system import pyqt5_xcb_support; ok, message = pyqt5_xcb_support(); print(message); raise SystemExit(not ok)" "$repo_root"; then
  echo 'PyQt5/X11: suporte xcb disponível.'
else
  echo 'AUSENTE: PyQt5 não tem suporte xcb; reinstale python3-pyqt5.'
fi
if ! id "$ui_user" >/dev/null 2>&1; then
  echo "AUSENTE: o usuário configurado para a UI ($ui_user) não existe. Use RADIO_UI_USER para informar o usuário correto."
elif pgrep -u "$ui_user" -f '(^|/)(Xorg|X)([[:space:]]|$)' >/dev/null; then
  echo "Sessão X11: servidor X encontrado para $ui_user."
else
  echo "AUSENTE: não foi encontrada sessão X11 do usuário $ui_user; habilite o autologin gráfico."
fi
if id "$ui_user" >/dev/null 2>&1 && command -v xinput >/dev/null && [[ -r "/home/$ui_user/.Xauthority" ]]; then
  if runuser -u "$ui_user" -- env DISPLAY=:0 XAUTHORITY="/home/$ui_user/.Xauthority" xinput --list 2>/dev/null | grep -Eiq 'ADS7846|Touchscreen'; then
    echo 'X/libinput: touchscreen visível para a sessão X11.'
  else
    echo 'AUSENTE: touchscreen não aparece em xinput; verifique a pilha X/libinput e o overlay.'
  fi
else
  echo 'AUSENTE: xinput/Xauthority indisponível; não foi possível validar a pilha X/libinput.'
fi

echo 'Áudio:'
aplay -l 2>/dev/null || true
