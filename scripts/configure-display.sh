#!/usr/bin/env bash
# Configura exclusivamente o LCD Waveshare/SpotPear 3.2 LCD V4 suportado.
set -euo pipefail

DRY=0
NON=0
ui_user=${SUDO_USER:-pi}
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY=1 ;;
    --non-interactive) NON=1 ;;
    --user=*) ui_user=${arg#*=} ;;
    *) echo "Opção inválida: $arg" >&2; exit 2 ;;
  esac
done
[[ $EUID -eq 0 ]] || { echo 'Execute com sudo.' >&2; exit 1; }

config_file=''
for candidate in /boot/firmware/config.txt /boot/config.txt; do
  [[ -e $candidate ]] || continue
  [[ -f $candidate && -r $candidate && -w $candidate ]] || {
    echo "ERRO: arquivo de boot inválido ou sem permissão de escrita: $candidate" >&2
    exit 1
  }
  config_file=$candidate
  break
done
[[ -n $config_file ]] || { echo 'ERRO: não encontrei /boot/firmware/config.txt nem /boot/config.txt.' >&2; exit 1; }

backup_dir=/var/backups/radio-movel-sdr
stamp=$(date +%Y%m%d-%H%M%S)
backup="$backup_dir/$(basename "$config_file").$stamp.bak"
overlay_dir="$(dirname "$config_file")/overlays"
driver_file="$overlay_dir/waveshare32b.dtbo"
driver_backup="$backup_dir/waveshare32b.dtbo.$stamp.bak"
driver_source=https://github.com/waveshareteam/LCD-show.git
managed_begin='# BEGIN radio-movel-sdr Waveshare 3.2 LCD V4'
managed_end='# END radio-movel-sdr Waveshare 3.2 LCD V4'

echo '=== Configuração de display ==='
echo "Modelo suportado: Waveshare/SpotPear 3.2 LCD V4 (waveshare32b)."
echo "Arquivo de boot selecionado: $config_file"

desired=$(cat <<EOF
$managed_begin
# LCD SPI 320x240; rotate=90 deixa a orientação em paisagem para a interface.
dtparam=spi=on
dtoverlay=waveshare32b:rotate=90
framebuffer_width=320
framebuffer_height=240
$managed_end
EOF
)

# Raspberry Pi OS does not ship this vendor overlay on every image.  Install only
# the dtbo from Waveshare's repository; do not run LCD32-show because it replaces
# the complete boot configuration and Xorg setup.
[[ -d $overlay_dir && -w $overlay_dir ]] || {
  echo "ERRO: diretório de overlays inválido ou sem escrita: $overlay_dir" >&2
  exit 1
}
driver_changed=0
if (( DRY )); then
  echo "[simulação] baixar $driver_source, validar e instalar o driver $driver_file se necessário"
else
  driver_stage=$(mktemp -d)
  trap 'rm -rf "$driver_stage"' EXIT
  git clone --depth 1 "$driver_source" "$driver_stage/LCD-show"
  source_driver="$driver_stage/LCD-show/waveshare32b-overlay.dtb"
  [[ -s $source_driver ]] || { echo 'ERRO: driver waveshare32b-overlay.dtb ausente no repositório do fabricante.' >&2; exit 1; }
  if [[ ! -f $driver_file ]] || ! cmp -s "$source_driver" "$driver_file"; then
    driver_changed=1
    [[ -e $driver_file ]] && cp -a "$driver_file" "$driver_backup"
    install -m 644 "$source_driver" "$driver_file"
    [[ -e $driver_backup ]] && echo "Backup do driver criado: $driver_backup"
    echo "Driver Waveshare instalado: $driver_file"
  fi
  rm -rf "$driver_stage"; trap - EXIT
fi

current=$(sed -n "/^${managed_begin}$/,/^${managed_end}$/p" "$config_file" || true)
changed=0
[[ $current == "$desired" ]] || changed=1
if (( changed )); then
  if (( DRY )); then
    echo "[simulação] criar backup $backup e atualizar bloco gerenciado em $config_file"
  else
    install -d -m 700 "$backup_dir"
    cp -a "$config_file" "$backup"
    tmp=$(mktemp "${config_file}.radio-movel.XXXXXX")
    trap 'rm -f "$tmp"' EXIT
    # Somente o bloco que este script possui é substituído; configuração do usuário é preservada.
    sed "/^${managed_begin}$/,/^${managed_end}$/d" "$config_file" >"$tmp"
    printf '\n%s\n' "$desired" >>"$tmp"
    cat "$tmp" >"$config_file"
    rm -f "$tmp"; trap - EXIT
    echo "Backup criado: $backup"
  fi
fi
if (( changed || driver_changed )); then
  echo 'ALTERADO: reinicialização obrigatória antes de detectar ou usar o LCD/touch.'
else
  echo 'Configuração do LCD já está atualizada; nenhuma reinicialização nova é necessária.'
fi

touches=()
for name_file in /sys/class/input/event*/device/name; do
  [[ -r $name_file ]] || continue
  name=$(<"$name_file")
  [[ $name =~ [Aa][Dd][Ss]7846|[Tt]ouchscreen ]] || continue
  event=$(basename "$(dirname "$(dirname "$name_file")")")
  touches+=("/dev/input/$event:$name")
done
if ((${#touches[@]} == 0)); then
  echo 'Touch: ainda não detectado. Se a configuração foi alterada, reinicie e execute: radioctl doctor'
  exit 0
fi
printf 'Touch detectado (mesma busca do doctor):\n'
printf '  %s\n' "${touches[@]}"
for item in "${touches[@]}"; do
  device=${item%%:*}
  if id "$ui_user" >/dev/null 2>&1 && runuser -u "$ui_user" -- test -r "$device"; then
    echo "  Permissão: $ui_user pode ler $device"
  else
    echo "  AVISO: $ui_user não pode ler $device; adicione-o ao grupo input e faça novo login."
  fi
done

home=$(getent passwd "$ui_user" | cut -d: -f6 || true)
xauth=${home:+$home/.Xauthority}
if command -v xinput >/dev/null && [[ -n $home && -r $xauth ]] && \
   runuser -u "$ui_user" -- env DISPLAY=:0 XAUTHORITY="$xauth" xinput --list 2>/dev/null | grep -Eiq 'ADS7846|Touchscreen'; then
  echo 'X11/libinput: touchscreen visível em DISPLAY=:0.'
  if (( ! NON && ! DRY )) && command -v xinput_calibrator >/dev/null; then
    read -r -p 'Abrir calibração visual do touch nesta sessão X11 agora? (s/N) ' answer
    if [[ $answer =~ ^[Ss]$ ]]; then
      echo 'Toque os quatro alvos da janela de calibração. Revise a saída antes de persistir alterações no Xorg.'
      runuser -u "$ui_user" -- env DISPLAY=:0 XAUTHORITY="$xauth" xinput_calibrator || \
        echo 'AVISO: calibração não foi concluída; use xinput --list e radioctl doctor após corrigir a sessão gráfica.'
    fi
  else
    echo 'Validação: toque a tela e confira o cursor; para calibração visual, na sessão X11 execute: xinput_calibrator'
  fi
else
  echo 'Touch no kernel, mas não validado na sessão X11. Após entrar no desktop, execute radioctl doctor e xinput --list.'
fi
