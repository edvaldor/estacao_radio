# Instalação
No Raspberry Pi OS Lite 32-bit ARMv7, conecte tela, SDR e áudio e execute `sudo ./scripts/install.sh`. Configure uma sessão gráfica X11 normal para o usuário que será selecionado pelo instalador: a aplicação usa essa sessão já existente e não inicia Xorg. Ao final, o instalador cria `/home/<usuário>/Desktop/radio-movel-sdr.desktop`. Entre na sessão gráfica e abra **Rádio Móvel SDR** com duplo clique nesse ícone. Nenhum serviço é habilitado para inicialização automática. Os pacotes X11 mínimos continuam obrigatórios e são instalados por `scripts/python-dependencies.sh`. O instalador verifica modelo, arquitetura, espaço, rede, tela/touch e RTL-SDR, pede a saída ALSA e preserva dados existentes. Para auditar sem modificar: `sudo ./scripts/install.sh --dry-run --non-interactive`. Se a janela não abrir, consulte `~/.local/state/radio-movel-sdr/launch.log` e execute `radioctl doctor`. Não rode este instalador nesta máquina Ubuntu/x86: ele recusa corretamente.

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
