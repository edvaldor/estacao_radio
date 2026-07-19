#!/usr/bin/env bash
# Migrate only known Waveshare-era profile lines; retain all other customization.
set -euo pipefail
user=${1:?user required}; home=$(getent passwd "$user" | cut -d: -f6)
profile="$home/.bash_profile"; backup_dir=${2:?backup dir required}
[[ -f $profile ]] || exit 0
tmp=$(mktemp); changed=0
while IFS= read -r line || [[ -n $line ]]; do
  if [[ $line =~ ^[[:space:]]*export[[:space:]]+FRAMEBUFFER=/dev/fb1[[:space:]]*$ ]] ||
     [[ $line =~ ^[[:space:]]*startx[[:space:]]+2\>[[:space:]]*/tmp/xorg_errors[[:space:]]*$ ]]; then
    printf '# Migrado pelo Rádio Móvel SDR: %s\n' "$line" >>"$tmp"; changed=1
  else printf '%s\n' "$line" >>"$tmp"; fi
done <"$profile"
if ((changed)); then
  mkdir -p "$backup_dir"; cp -a "$profile" "$backup_dir/bash_profile.before-x-migration"
  install -o "$user" -g "$(id -gn "$user")" -m 644 "$tmp" "$profile"
  echo "Migração: removido startx/FRAMEBUFFER antigo de $profile (backup em $backup_dir)."
fi
rm -f "$tmp"
