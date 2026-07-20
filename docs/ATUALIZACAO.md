# Atualização e recuperação

Use `sudo radioctl update --check-only` para consultar tags e `sudo radioctl update` para instalar a última tag estável. O comando atualiza por **tag**, não pelo último commit da branch: uma alteração só chegará ao Pi quando for publicada em uma tag, ou quando você indicar a tag com `sudo radioctl update --version TAG`. Antes, o atualizador cria backup de `/var/lib/radio-movel-sdr`, atualiza os pacotes APT declarados (`python3`, venv, PyQt5, gpiozero, rtl-sdr, ALSA e X mínimo), recria o ambiente Python se necessário, executa `compileall` e recria o lançador da área de trabalho. No fluxo principal, a aplicação continua sendo aberta por duplo clique no atalho da área de trabalho, dentro da sessão gráfica existente; a atualização não habilita serviço nem inicialização automática.

O atualizador **não** altera a versão principal do Python nem executa `apt upgrade` no sistema inteiro: upgrades de distribuição exigem decisão e backup do administrador. Se a validação do código falhar, o commit anterior é restaurado automaticamente; use `sudo radioctl update --rollback` para reverter o código manualmente. Atualizações de pacotes APT não são revertidas automaticamente. A atualização automática permanece desativada.

## Reinstalação do lançador

Conecte por SSH e execute exatamente os comandos abaixo. Eles atualizam o
checkout que você usou para instalar e executam novamente o instalador, que
preserva `settings.json` e favoritos.

```bash
cd ~/radio-movel-sdr
git fetch origin
git pull --ff-only origin main
sudo ./scripts/install.sh --non-interactive
```

Se o clone estiver em outro diretório, substitua somente a primeira linha pelo
caminho correto. Depois, entre no desktop do usuário selecionado e abra **Rádio Móvel SDR** com
duplo clique no atalho. Para encerrar após a atualização, feche a janela (por
exemplo, com `Alt+F4`); a aplicação encerra a recepção e o áudio. Confirme que a
atualização não ativou execução no boot:

```bash
systemctl is-enabled radio-movel-sdr.service
systemctl is-active radio-movel-sdr.service
```

Os resultados esperados são `not-found` (ou `disabled` para uma unidade antiga
mantida manualmente) e `inactive`. Para atualizar uma instalação já em `/opt` por
uma tag, use `sudo radioctl update`; se a validação do código falhar, o atualizador
restaura automaticamente o commit anterior e grava a causa em
`/var/log/radio-movel-sdr-update.log`.

## Raspberry Pi OS Lite (opt-in)

Se você tiver escolhido deliberadamente o fluxo Lite com a unidade
`radio-movel-sdr.service`, atualize o código normalmente, mas trate a unidade
separadamente: ela é quem inicia o rádio no boot. Depois de atualizar, recarregue e
reinicie a unidade somente se quiser manter esse comportamento de aparelho dedicado:

```bash
sudo systemctl daemon-reload
sudo systemctl restart radio-movel-sdr.service
```

Para migrar para o fluxo principal com ambiente gráfico e impedir execução no boot,
desabilite a unidade e execute novamente `sudo ./scripts/install.sh` para recriar o
atalho da área de trabalho:

```bash
sudo systemctl disable --now radio-movel-sdr.service
sudo rm -f /etc/systemd/system/radio-movel-sdr.service
sudo systemctl daemon-reload
```
