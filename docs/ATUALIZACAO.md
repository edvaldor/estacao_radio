# Atualização e recuperação

Use `sudo radioctl update --check-only` para consultar tags e `sudo radioctl update` para instalar a última tag estável. Antes, o atualizador cria backup de `/var/lib/radio-movel-sdr`, atualiza os pacotes APT declarados (`python3`, venv, PyQt5, gpiozero, rtl-sdr, ALSA e X mínimo), recria o ambiente Python se necessário e executa `compileall` antes de reiniciar o serviço.

O atualizador **não** altera a versão principal do Python nem executa `apt upgrade` no sistema inteiro: upgrades de distribuição exigem decisão e backup do administrador. Se a validação do código falhar, o commit anterior é restaurado automaticamente; use `sudo radioctl update --rollback` para reverter o código manualmente. Atualizações de pacotes APT não são revertidas automaticamente. A atualização automática permanece desativada.
