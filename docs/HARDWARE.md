# Hardware
Alvo: Raspberry Pi 2 Model B ARMv7, Raspberry Pi OS Lite 32-bit, Waveshare/SpotPear 3.2 LCD V4 (overlay `waveshare32b`, SPI, ADS7846) e RTL2832U/R820T. Os pinos opcionais são GPIO18/23/24 (anterior/receber/próximo). O processo usa apenas `rtl_fm`; não há código de transmissão. Áudio é ALSA e pode ser P2, HDMI ou USB. O indicador de nível futuro será áudio, nunca S-meter RF verdadeiro.

## Display suportado

O instalador suporta **somente** a Waveshare/SpotPear **3.2 LCD V4** compatível com o overlay do kernel `waveshare32b`. `scripts/configure-display.sh` seleciona o arquivo existente `/boot/firmware/config.txt` (Raspberry Pi OS atual) ou `/boot/config.txt` (imagens antigas), valida que ele é um arquivo gravável, instala o driver `waveshare32b.dtbo` do repositório oficial `waveshareteam/LCD-show` no diretório `overlays` correspondente e acrescenta um bloco identificado com:

- `dtparam=spi=on`;
- `dtoverlay=waveshare32b:rotate=90`;
- framebuffer SPI de `320x240`.

`rotate=90` é a orientação paisagem adotada pela aplicação. A tela pode ficar girada ou o toque pode não coincidir em clones, revisões V1/V2/V3, telas DSI/HDMI e controladores diferentes (por exemplo XPT2046): esses modelos **não são configurados nem validados** por este projeto e exigem o overlay e os parâmetros do fornecedor. Não acrescente um segundo overlay para a mesma tela.

Ao alterar o bloco, o script cria uma cópia preservada em `/var/backups/radio-movel-sdr/config.txt.<data>.bak`; se substituir um driver já presente, preserva também `waveshare32b.dtbo.<data>.bak`. A reinicialização é obrigatória: SPI, framebuffer e ADS7846 só são carregados no boot. O script não executa o `LCD32-show` do fabricante, pois ele substituiria todo o `config.txt` e a configuração X11 existente. Depois do reboot, `radioctl doctor` localiza o touch pelo nome em `/sys/class/input` (não por `eventN`), confere permissões do usuário e sua presença no X11/libinput.

Para desfazer a alteração, restaure o backup correspondente ao arquivo de boot usado, por exemplo:

```bash
sudo cp -a /var/backups/radio-movel-sdr/config.txt.20260720-120000.bak /boot/firmware/config.txt
# Apenas se o script informou backup do driver:
sudo cp -a /var/backups/radio-movel-sdr/waveshare32b.dtbo.20260720-120000.bak /boot/firmware/overlays/waveshare32b.dtbo
sudo reboot
```
