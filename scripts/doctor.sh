#!/usr/bin/env bash
set -u
echo '=== Diagnóstico Rádio Móvel SDR ==='; echo "Sistema: $(. /etc/os-release; echo "$PRETTY_NAME")"; echo "Kernel: $(uname -a)"
echo 'RTL-SDR:'; command -v rtl_test >/dev/null && timeout 15 rtl_test -t || echo 'rtl_test não disponível ou SDR não detectado.'
echo 'Tela/framebuffer:'; find /sys/class/graphics -name fb\* -printf '%f\n' 2>/dev/null || true
echo 'Touchscreen (por nome, nunca event fixo):'; for f in /sys/class/input/event*/device/name; do [[ -r $f ]] && { n=$(cat "$f"); [[ $n =~ [Aa][Dd][Ss]7846|[Tt]ouchscreen ]] && echo "$f: $n"; }; done
echo 'SPI:'; ls /dev/spidev* 2>/dev/null || echo 'SPI não detectado.'; echo 'Áudio:'; aplay -l 2>/dev/null || true
