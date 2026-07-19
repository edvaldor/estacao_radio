# Atualização e recuperação

Use `sudo radioctl update --check-only` para consultar tags e `sudo radioctl update` para instalar a última tag estável. O comando atualiza por **tag**, não pelo último commit da branch: uma alteração só chegará ao Pi quando for publicada em uma tag, ou quando você indicar a tag com `sudo radioctl update --version TAG`. Antes, o atualizador cria backup de `/var/lib/radio-movel-sdr`, atualiza os pacotes APT declarados (`python3`, venv, PyQt5, gpiozero, rtl-sdr, ALSA e X mínimo), recria o ambiente Python se necessário, executa `compileall`, atualiza `radio-movel-sdr.service`, que é a única responsável por Xorg e pela UI, e valida que ambos permanecem ativos.

O atualizador **não** altera a versão principal do Python nem executa `apt upgrade` no sistema inteiro: upgrades de distribuição exigem decisão e backup do administrador. Se a validação do código falhar, o commit anterior é restaurado automaticamente; use `sudo radioctl update --rollback` para reverter o código manualmente. Atualizações de pacotes APT não são revertidas automaticamente. A atualização automática permanece desativada.

## Atualização da correção de inicialização X

Conecte por SSH e execute exatamente os comandos abaixo. Eles atualizam o
checkout que você usou para instalar e executam novamente o instalador, que
preserva `settings.json`, favoritos e as linhas pessoais do `.bash_profile`.

```bash
cd ~/radio-movel-sdr
git fetch origin
git pull --ff-only origin main
sudo ./scripts/install.sh --non-interactive
sudo systemctl restart radio-movel-sdr.service
radioctl status
radioctl logs
```

Se o clone estiver em outro diretório, substitua somente a primeira linha pelo
caminho correto. Não use `startx` manualmente após a migração: o serviço é o
único iniciador de X. Para atualizar uma instalação já em `/opt` por uma tag,
use `sudo radioctl update`; se a validação detectar que X ou a interface fechou,
o atualizador restaura automaticamente o commit e a unidade anteriores e grava
a causa em `/var/log/radio-movel-sdr-update.log`.
