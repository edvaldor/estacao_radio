# Instalação
No Raspberry Pi OS Lite 32-bit ARMv7, conecte tela, SDR e áudio e execute `sudo ./scripts/install.sh`. Configure uma sessão gráfica X11 normal para o usuário que será selecionado pelo instalador: a aplicação usa essa sessão já existente e não inicia Xorg. Ao final, o instalador cria `/home/<usuário>/Desktop/radio-movel-sdr.desktop`. Entre na sessão gráfica e abra **Rádio Móvel SDR** com duplo clique nesse ícone. Nenhum serviço é habilitado para inicialização automática. Os pacotes X11 mínimos continuam obrigatórios e são instalados por `scripts/python-dependencies.sh`. O instalador verifica modelo, arquitetura, espaço, rede, SPI/touch e RTL-SDR, pede a saída ALSA e preserva dados existentes. Para auditar sem modificar: `sudo ./scripts/install.sh --dry-run --non-interactive`. Se a janela não abrir, consulte `~/.local/state/radio-movel-sdr/launch.log` e execute `radioctl doctor`. Não rode este instalador nesta máquina Ubuntu/x86: ele recusa corretamente.

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
