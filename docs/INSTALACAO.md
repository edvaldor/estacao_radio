# Instalação

## Fluxo principal — Raspberry Pi OS 32-bit com ambiente gráfico

Use **Raspberry Pi OS 32-bit com ambiente gráfico** no Raspberry Pi 2. Não use a imagem Lite para este fluxo. Antes da instalação, entre no desktop pelo menos uma vez com o usuário que usará o rádio, conecte tela, RTL-SDR e áudio, configure a rede e habilite SPI/overlay conforme a tela.

No clone do projeto, execute:

```bash
sudo ./scripts/install.sh
```

O instalador verifica modelo, arquitetura, espaço, rede, tela/touch e RTL-SDR, pede a saída ALSA e preserva dados existentes. Ele instala as dependências necessárias e cria o atalho `/home/<usuário>/Desktop/radio-movel-sdr.desktop` para o usuário selecionado. Para auditar sem modificar: `sudo ./scripts/install.sh --dry-run --non-interactive`. Não rode este instalador em Ubuntu/x86: ele recusa corretamente.

### Abrir e encerrar o rádio

1. Entre no desktop do usuário selecionado pelo instalador.
2. Localize o ícone **Rádio Móvel SDR** na área de trabalho; ele corresponde a `~/Desktop/radio-movel-sdr.desktop`.
3. Dê **duplo clique** no ícone. O lançador abre o programa dentro da sessão gráfica atual e registra mensagens em `~/.local/state/radio-movel-sdr/launch.log`.
4. Para encerrar, feche a janela do rádio — por exemplo, com `Alt+F4`. A aplicação para o receptor e o áudio ao ser fechada. Para encerrar remotamente, entre como o usuário do desktop e execute:

```bash
pkill -f '/opt/radio-movel-sdr/venv/bin/python -m app.main'
```

A instalação gráfica não configura inicialização automática. Ela desabilita e remove uma eventual unidade `radio-movel-sdr.service`; portanto, o ícone só abre o rádio quando recebe o duplo clique. Confirme que não há abertura no boot com:

```bash
systemctl is-enabled radio-movel-sdr.service
systemctl is-active radio-movel-sdr.service
```

O resultado esperado é `not-found` (ou `disabled` se uma unidade antiga foi deixada manualmente) no primeiro comando e `inactive` no segundo. Se a janela não abrir, consulte o log acima e execute `radioctl doctor`.

## Fluxo alternativo e opt-in — Raspberry Pi OS Lite 32-bit

Use este fluxo **somente** se desejar transformar o Pi em um aparelho dedicado, sem desktop convencional, iniciando o rádio via systemd. Ele é separado do fluxo gráfico: não instale ou habilite esta unidade em uma instalação com ambiente gráfico, pois ela cria e controla sua própria sessão Xorg.

Primeiro instale os componentes no Lite com `sudo ./scripts/install.sh`. Depois, substitua `pi` pelo usuário escolhido e habilite explicitamente a unidade:

```bash
sudo sed 's/__USER__/pi/g' /opt/radio-movel-sdr/systemd/radio-movel-sdr.service \
  | sudo tee /etc/systemd/system/radio-movel-sdr.service >/dev/null
sudo systemctl daemon-reload
sudo systemctl enable --now radio-movel-sdr.service
```

Nesse fluxo alternativo, a unidade é a opção que abre o rádio no boot. Para pará-lo ou impedir novas inicializações, use:

```bash
sudo systemctl disable --now radio-movel-sdr.service
```

Para voltar ao fluxo principal com desktop, mantenha a unidade desabilitada/removida e execute novamente o instalador gráfico para recriar o atalho.

## Configuração de display e toque

Antes de copiar a aplicação, `scripts/install.sh` chama `scripts/configure-display.sh`. Para a única tela suportada, Waveshare/SpotPear 3.2 LCD V4, ele encontra e valida `/boot/firmware/config.txt` ou `/boot/config.txt`, baixa o driver oficial `waveshare32b-overlay.dtb` de `waveshareteam/LCD-show` e o instala como `overlays/waveshare32b.dtbo`, faz backup em `/var/backups/radio-movel-sdr/` e grava um bloco gerenciado com SPI, `dtoverlay=waveshare32b:rotate=90` e framebuffer `320x240`. O backup só é criado quando há uma alteração efetiva. O instalador não executa `LCD32-show`, para não substituir o arquivo de boot inteiro nem a configuração X11.

Quando o script informar `ALTERADO`, **reinicie obrigatoriamente** antes de esperar imagem ou touch; o ADS7846 e o framebuffer são inicializados no boot:

```bash
sudo reboot
```

Após retornar ao desktop, execute `radioctl doctor`. Ele usa o nome do controlador em sysfs, portanto não depende do número variável `/dev/input/eventN`, verifica se o usuário da interface pode lê-lo e confere `xinput` na sessão X11. Durante uma instalação interativa com uma sessão X11 disponível, o instalador oferece `xinput_calibrator`; toque os quatro alvos. Caso tenha reiniciado ou a sessão ainda não existisse, execute a calibração **dentro do desktop**:

```bash
xinput_calibrator
radioctl doctor
```

Não aplique cegamente a saída da calibração em `/etc/X11/xorg.conf.d`: revise-a para o driver `libinput` e para a rotação escolhida. Em geral, o overlay já entrega a rotação correta. Para reverter a configuração de boot, restaure o backup referente ao arquivo que foi alterado e reinicie:

```bash
sudo cp -a /var/backups/radio-movel-sdr/config.txt.<data>.bak /boot/firmware/config.txt
# Se houver backup do driver na mesma execução:
sudo cp -a /var/backups/radio-movel-sdr/waveshare32b.dtbo.<data>.bak /boot/firmware/overlays/waveshare32b.dtbo
sudo reboot
```

Em imagens que usam `/boot/config.txt`, substitua o destino no comando. Outras revisões Waveshare/SpotPear, telas HDMI/DSI, clones e controladores diferentes não são suportados por este bloco e devem usar exclusivamente o procedimento do fabricante.

## Detecção e validação do RTL-SDR

Ao final da instalação, o instalador executa uma detecção RTL-SDR com timeout de 10 segundos usando `rtl_test`.

### Quando RTL-SDR é detectado

Em modo interativo (`sudo ./scripts/install.sh` sem `--non-interactive`):
1. Pergunta se deseja fazer teste de sintonia
2. Se sim: inicia `rtl_fm -f 91.9M -M wfm` durante 5 segundos
3. Toca áudio no dispositivo ALSA selecionado
4. Pergunta se você ouviu a emissora
5. Se confirmado: marca RTL-SDR como validado

Em modo não-interativo (`sudo ./scripts/install.sh --non-interactive`):
- Salta o teste de sintonia
- Apenas registra que RTL-SDR foi detectado
- Instala com sucesso

### Quando RTL-SDR NÃO é detectado

**Causas possíveis:**
- USB desconectado ou com problema
- Driver DVB (`dvb_usb_rtl28xxu`) ocupando o dispositivo
- Falta de permissões (udev rules)

**Em modo interativo, o instalador oferece:**

```
Opções:
  [1] Apenas demonstração (--demo, sem SDR)
  [2] Conectar RTL-SDR e retomar
  [3] Abortar instalação
```

Escolha **[1]** para instalar mesmo sem SDR e testar com `--demo`:

```bash
cd /opt/radio-movel-sdr
/opt/radio-movel-sdr/venv/bin/python -m app.main --demo
```

Escolha **[2]** para desconectar, conectar o SDR e executar novamente:

```bash
sudo ./scripts/install.sh
```

**Em modo não-interativo, o instalador registra o resultado e prossegue sem SDR.**

### Remover driver DVB ocupando RTL-SDR

Se `rtl_test` informar que o dispositivo está ocupado:

```bash
sudo modprobe -r dvb_usb_rtl28xxu
sudo ./scripts/install.sh
```

Para manté-lo descarregado permanentemente, crie uma blacklist:

```bash
echo 'blacklist dvb_usb_rtl28xxu' | sudo tee /etc/modprobe.d/rtl-sdr-blacklist.conf
sudo update-initramfs -u
```

### Validar após instalação

Use `radioctl rtl-test` ou `radioctl doctor` para diagnosticar problemas posteriores.
