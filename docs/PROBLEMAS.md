# Problemas
## A interface não abriu

A instalação deve ser executada como root: `sudo ./scripts/install.sh`. Ela instala uma unidade systemd de usuário para o `pi`, habilitada em `graphical-session.target`; a sessão gráfica X11 com autologin do `pi` é necessária. A unidade recebe `DISPLAY=:0`, `XAUTHORITY=/home/pi/.Xauthority` e o `XDG_RUNTIME_DIR` da sessão. Verifique o estado e o erro sem perder o diagnóstico:

```bash
radioctl status
radioctl logs
radioctl restart
```

Se a instalação foi feita por uma revisão anterior, execute novamente o instalador para migrar da unidade de sistema para a unidade de usuário.

## Outros diagnósticos

Execute `radioctl doctor` e `radioctl logs`. Se houver `usb_claim_interface error -6`, o kernel DVB pode estar usando o SDR: confirme no diagnóstico antes de criar blacklist, faça backup de qualquer configuração e reinicie. Sem SDR, inicie com `--demo`; sem GPIO ou touch, a aplicação continua pela interface disponível.

## Touchscreen ADS7846/Waveshare não responde

O número de evento **não é fixo**: USB, HDMI e outros dispositivos podem mudar o
`eventN` a cada boot. Faça o diagnóstico como root ou com `sudo`; o comando
também informa se o usuário que executa a interface (`pi`, ou o valor de
`RADIO_UI_USER`) tem leitura no device encontrado:

```bash
radioctl doctor
cat /proc/bus/input/devices
```

Procure o bloco cujo nome é `ADS7846 Touchscreen`. O campo `Handlers` contém o
`eventN` atualmente associado; use esse valor somente para a conferência daquele
boot. O `radioctl doctor` encontra o mesmo dispositivo pelo nome em sysfs e
mostra o caminho correspondente, por exemplo `/dev/input/event3`, sem assumir
que será sempre esse número.

Em seguida confirme a configuração de boot. Em Raspberry Pi OS recente o arquivo
normalmente é `/boot/firmware/config.txt`; em instalações antigas pode ser
`/boot/config.txt`:

```bash
sudo grep -Ev '^\s*#|^\s*$' /boot/firmware/config.txt | grep -E 'dtparam=spi=on|dtoverlay=waveshare32b'
# Se o primeiro arquivo não existir, repita usando /boot/config.txt.
```

Devem aparecer `dtparam=spi=on` e `dtoverlay=waveshare32b` (com os parâmetros
adicionais recomendados pelo fornecedor da revisão física da tela). Após alterar
o overlay ou SPI, reinicie. Se o diagnóstico indicar que `/dev/spidev*`, o
overlay ou o ADS7846 está **AUSENTE**, corrija primeiro a configuração indicada;
não crie regra baseada em `/dev/input/eventN`.

Se o device existir mas a permissão estiver negada, descubra o grupo proprietário
com `ls -l /dev/input/eventN` usando o caminho exibido pelo diagnóstico, adicione
o usuário da UI a esse grupo (normalmente `input`) e encerre/inicie a sessão do
usuário para renovar os grupos:

```bash
sudo usermod -aG input pi
```

## Configuração Qt de entrada

O modo selecionado por este projeto é **sessão X11**, não framebuffer direto. A
unidade `radio-movel-sdr.service` inicia a UI como `pi`, com `QT_QPA_PLATFORM=xcb`, `DISPLAY=:0` e o `XAUTHORITY` desse
usuário. Portanto, não defina `QT_QPA_EVDEV_TOUCHSCREEN_PARAMETERS` nem force
`linuxfb`/`eglfs` nessa instalação: a entrada é entregue pelo Xorg e libinput.
O instalador instala `xserver-xorg-input-libinput` e `xinput`. O `radioctl
doctor` valida o plugin `xcb` do PyQt5, a sessão X11 de `pi` e, quando o cookie
X estiver disponível, se o ADS7846 é visível na pilha X/libinput. Em caso de
falha, confira também:

```bash
sudo -u pi DISPLAY=:0 XAUTHORITY=/home/pi/.Xauthority xinput --list
radioctl status
radioctl logs
```

Para uma futura instalação em **framebuffer direto**, isso é uma troca de modo,
não apenas uma variável de ambiente: antes de desativar X11, confirme que o
PyQt5 instalado contém o backend escolhido (`linuxfb` ou `eglfs`) e o suporte de
entrada `evdev`/`libinput`. Configure explicitamente `QT_QPA_PLATFORM` e o
device detectado naquele boot (por exemplo,
`QT_QPA_EVDEV_TOUCHSCREEN_PARAMETERS=/dev/input/eventN`); não reutilize um
`eventN` documentado ou de boot anterior. Essa combinação não é configurada nem
validada pela unidade X11 atual.

## A tela apareceu e voltou ao prompt

A causa conhecida deste sintoma é haver **dois iniciadores do X**: a receita antiga
no `/home/pi/.bash_profile` executa `startx`, enquanto o serviço do rádio tenta
abrir o mesmo display `:0`. O segundo X encerra ou perde o display e o console
volta a aparecer. Esta versão usa somente `radio-movel-sdr.service`; nunca deixe
`startx` em `.bash_profile` para o rádio. O instalador e o atualizador comentam
somente as duas linhas antigas reconhecidas, guardando uma cópia em
`/var/backups/radio-movel-sdr/`.

Pelo SSH, recupere primeiro o console sem reiniciar:

```bash
sudo systemctl stop radio-movel-sdr.service
radioctl status
radioctl logs
sudo radioctl doctor
```

Veja a causa exata no journal. O `doctor` também mostra Xorg, locks, framebuffer,
touch, grupos e áudio. Não apague `/tmp/.X0-lock` manualmente: o lançador só o
remove se o PID escrito nele não estiver vivo. Depois de atualizar/reinstalar,
restaure a interface sem reboot:

```bash
cd /opt/radio-movel-sdr
git fetch --tags
git checkout <tag-ou-commit-aprovado>
sudo ./scripts/install.sh --non-interactive
sudo systemctl restart radio-movel-sdr.service
radioctl status
```

Para testar sem RTL-SDR, pare o serviço e inicie uma sessão de demonstração
controlada (ela usa o mesmo X do serviço):

```bash
sudo systemctl stop radio-movel-sdr.service
sudo -u pi HOME=/home/pi DISPLAY=:0 XAUTHORITY=/home/pi/.Xauthority \
  /opt/radio-movel-sdr/venv/bin/python -m app.main --demo
sudo systemctl start radio-movel-sdr.service
```

Se uma saída ALSA for inválida ou o RTL-SDR faltar, a mensagem deve aparecer na
janela e no journal; a sessão gráfica continua aberta. Botões GPIO ausentes ou
com erro também são apenas registrados e não devem fechar a interface.
