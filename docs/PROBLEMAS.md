# Problemas

## A interface não abriu

Execute a instalação como root: `sudo ./scripts/install.sh`. Ela cria o lançador
`/home/<usuário>/Desktop/radio-movel-sdr.desktop` para o usuário selecionado. Entre
na sessão gráfica desse usuário e abra **Rádio Móvel SDR** com duplo clique. O
lançador usa a sessão X11 já aberta; ele não inicia Xorg e não existe um serviço
`radio-movel-sdr.service` habilitado para iniciar a interface automaticamente.

Consulte o registro acessível ao usuário e o diagnóstico:

```bash
cat ~/.local/state/radio-movel-sdr/launch.log
radioctl doctor
```

Se o lançador não estiver na área de trabalho, repare a instalação no clone do
projeto:

```bash
cd ~/radio-movel-sdr
sudo ./scripts/install.sh --non-interactive
```

## Touchscreen ADS7846/Waveshare não responde

O número de evento **não é fixo**: USB, HDMI e outros dispositivos podem mudar o
`eventN` a cada boot. Execute `radioctl doctor` e `cat /proc/bus/input/devices`;
procure o bloco `ADS7846 Touchscreen`. O campo `Handlers` contém o `eventN` atual,
mas use-o somente para a conferência daquele boot. O diagnóstico encontra o mesmo
dispositivo pelo nome em sysfs e mostra o caminho correspondente.

Confirme também `dtparam=spi=on` e `dtoverlay=waveshare32b:rotate=90` no arquivo de boot
(`/boot/firmware/config.txt` em instalações recentes ou `/boot/config.txt` nas
antigas). Se a permissão do device for negada, adicione o usuário da UI ao grupo
proprietário, normalmente `input`, e encerre/inicie a sessão para renovar os grupos:

```bash
sudo usermod -aG input pi
```

Se o instalador acabou de criar/atualizar o bloco do display, o reboot não é opcional: restaure a energia ou execute `sudo reboot` antes de diagnosticar. Confira qual arquivo foi alterado na saída da instalação. Para voltar ao estado anterior, restaure o backup criado pelo configurador e reinicie (ajuste o destino para `/boot/config.txt` nas imagens antigas):

```bash
sudo cp -a /var/backups/radio-movel-sdr/config.txt.<data>.bak /boot/firmware/config.txt
# Se o instalador também salvou o driver anterior:
sudo cp -a /var/backups/radio-movel-sdr/waveshare32b.dtbo.<data>.bak /boot/firmware/overlays/waveshare32b.dtbo
sudo reboot
```

O bloco automatizado é específico para Waveshare/SpotPear 3.2 LCD V4 (`waveshare32b`, ADS7846, 320x240 em paisagem). Ele instala o driver em `overlays/waveshare32b.dtbo` e faz backup do driver anterior quando existir; não execute adicionalmente `LCD32-show`, pois ele substitui toda a configuração de boot. Não misture o overlay dele com a receita de outra revisão, clone, tela HDMI/DSI ou touch XPT2046. Nesses casos, restaure o backup e siga o manual do fabricante.

## Configuração Qt de entrada

O modo selecionado é **sessão X11**, não framebuffer direto. O lançador configura
`QT_QPA_PLATFORM=xcb` e herda `DISPLAY` e `XAUTHORITY` da sessão gráfica do usuário.
Não defina `QT_QPA_EVDEV_TOUCHSCREEN_PARAMETERS` nem force `linuxfb`/`eglfs`: a
entrada é entregue pelo Xorg e libinput. Em caso de falha, confira:

```bash
xinput --list
tail -n 100 ~/.local/state/radio-movel-sdr/launch.log
```

Se o dispositivo aparecer em `xinput` mas o toque estiver deslocado, execute `xinput_calibrator` **na sessão gráfica do usuário**, toque os quatro alvos e revise a configuração gerada para `libinput` antes de gravá-la em `/etc/X11/xorg.conf.d`. A calibração não funciona adequadamente via SSH sem `DISPLAY`/`XAUTHORITY` da sessão do desktop.

## O lançador não abre uma segunda janela

Isso é esperado: o lançador usa um bloqueio para impedir múltiplas instâncias.
Feche a janela existente antes de abrir novamente. Se ela não estiver visível,
verifique os processos e o registro:

```bash
pgrep -af 'python.*app.main'
tail -n 100 ~/.local/state/radio-movel-sdr/launch.log
```

Para testar sem RTL-SDR, execute na própria sessão gráfica:

```bash
cd /opt/radio-movel-sdr
/opt/radio-movel-sdr/venv/bin/python -m app.main --demo
```
