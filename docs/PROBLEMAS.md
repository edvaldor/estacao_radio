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

Confirme também `dtparam=spi=on` e `dtoverlay=waveshare32b` no arquivo de boot
(`/boot/firmware/config.txt` em instalações recentes ou `/boot/config.txt` nas
antigas). Se a permissão do device for negada, adicione o usuário da UI ao grupo
proprietário, normalmente `input`, e encerre/inicie a sessão para renovar os grupos:

```bash
sudo usermod -aG input pi
```

## Configuração Qt de entrada

O modo selecionado é **sessão X11**, não framebuffer direto. O lançador configura
`QT_QPA_PLATFORM=xcb` e herda `DISPLAY` e `XAUTHORITY` da sessão gráfica do usuário.
Não defina `QT_QPA_EVDEV_TOUCHSCREEN_PARAMETERS` nem force `linuxfb`/`eglfs`: a
entrada é entregue pelo Xorg e libinput. Em caso de falha, confira:

```bash
xinput --list
tail -n 100 ~/.local/state/radio-movel-sdr/launch.log
```

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
