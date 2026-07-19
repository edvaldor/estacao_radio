# Rádio Móvel SDR

Receptor portátil **somente de recepção** para Raspberry Pi 2, RTL-SDR RTL2832U/R820T e display resistivo Waveshare/SpotPear 3,2". Ele oferece AM aeronáutico, FM estreita, FM comercial, favoritos, scanner, persistência, diagnóstico e modo de demonstração. Não contém transmissão, gravação automática, decodificação digital, waterfall, GNU Radio, Gqrx ou acesso a comunicações criptografadas.

> **Estado de validação:** este repositório foi testado em ambiente Ubuntu x86 sem o hardware. O instalador foi projetado para recusar esse ambiente; a validação de SDR, tela, áudio e GPIO no Pi real ainda é necessária.

## Recursos

- Interface PyQt5 em tela cheia, botões grandes para toque resistivo e fallback quando touch/GPIO não existem.
- Modos iniciais: Aviação (AM, 118–137 MHz configurável), FM comercial (WFM, 88–108 MHz) e sintonia livre AM/FM/WFM.
- Passos, ganho automático/manual, squelch, volume ALSA persistente e restauração da última sintonia.
- Backend `rtl_fm` + `aplay` sem shell nem interpolação de entrada.
- Botões opcionais: GPIO18 anterior, GPIO23 iniciar/parar e GPIO24 próximo.
- Diagnóstico do ADS7846 por nome/caminho sysfs (não fixa `/dev/input/eventN`), SPI/framebuffer/ALSA/RTL-SDR.
- Serviços, atualização com rollback, backup/restauração e `radioctl` em português.

## Instalação para leigos

1. Instale Raspberry Pi OS Lite **32-bit** no Pi 2 e conecte a tela, o RTL-SDR, a antena e uma saída de áudio.
2. Configure o overlay/touchscreen conforme o fornecedor da tela (normalmente `waveshare32b`), habilite SPI e confirme Wi-Fi/SSH.
3. No Pi, execute:

```bash
git clone URL_DO_REPOSITORIO radio-movel-sdr
cd radio-movel-sdr
sudo ./scripts/install.sh
```

O instalador instala/atualiza os pacotes APT necessários (`python3`, `python3-venv`, PyQt5, gpiozero, rtl-sdr, ALSA e X mínimo), cria `/opt/radio-movel-sdr/venv` com acesso apenas aos pacotes do sistema e confirma Raspberry Pi, ARMv7 e Raspberry Pi OS; verifica internet e pelo menos 900 MB livres; lista áudio ALSA e guarda backups em `/var/backups/radio-movel-sdr`. Ele não sobrescreve `settings.json` ou `presets.json` existentes. Para ver ações sem alterar nada: `sudo ./scripts/install.sh --dry-run --non-interactive`.

Ao terminar a instalação, o serviço já abre a interface e também a abre automaticamente nos próximos boot. Ele é um serviço do sistema, portanto o autologin não é necessário nem interfere nesse início. O instalador só termina com sucesso se o serviço estiver habilitado e ativo. Caso necessário: `sudo systemctl restart radio-movel-sdr`. Para confirmar a causa de uma tela que não abriu, execute `radioctl status` e `radioctl logs`.

## Uso sem teclado

- **Anterior/Próximo:** altera a frequência pelo passo atual.
- **Receber:** inicia ou encerra `rtl_fm` e `aplay` corretamente antes de trocar a sintonia.
- **Favoritos/Scanner:** estes botões estão explicitamente marcados como **não implementados na interface atual**. Os dados em `presets.json` e o módulo scanner são preparação para a próxima versão, mas não iniciam uma varredura.
- **Volume:** ajusta o controle ALSA `Master` com `amixer` e persiste o valor quando o controle existe.
- **Demonstração:** execute manualmente `cd /opt/radio-movel-sdr && /opt/radio-movel-sdr/venv/bin/python -m app.main --demo` sem SDR.

Os exemplos aeronáuticos têm rótulos genéricos, não frequências locais verificadas. Confirme qualquer frequência operacional em fonte oficial antes do uso.

## Administração e recuperação

| Comando | Função |
|---|---|
| `radioctl status/start/stop/restart` | Controla o serviço. |
| `radioctl logs` | Mostra logs do journal. |
| `radioctl doctor` | Diagnostica SDR, touch, SPI, framebuffer e áudio. |
| `radioctl rtl-test` | Executa teste do receptor. |
| `radioctl audio` | Lista dispositivos ALSA. |
| `radioctl backup [arquivo]` | Salva favoritos e configurações. |
| `radioctl restore arquivo.tar.gz` | Restaura configurações. |
| `radioctl update --check-only` | Consulta atualização estável. |
| `radioctl update` / `radioctl update --rollback` | Atualiza por tag ou volta ao commit anterior. |

A atualização instala a última **tag estável publicada** (ou uma tag informada com `--version`), atualiza novamente os componentes APT declarados, atualiza a unidade systemd instalada e valida a aplicação antes de reiniciar o serviço. Portanto, um commit que ainda não recebeu tag não é instalado por `radioctl update`. Ela **não** faz upgrade de versão principal do Python ou do sistema operacional, pois isso pode quebrar o Raspberry Pi OS; essas atualizações devem ser feitas pelo administrador via APT. A atualização automática é deliberadamente desativada. Consulte [ATUALIZACAO.md](docs/ATUALIZACAO.md) e [PROBLEMAS.md](docs/PROBLEMAS.md) para recuperação.

## Arquitetura e decisões

`Receiver` valida frequência, modulação, ganho, squelch e taxa antes de iniciar `rtl_fm` com lista de argumentos (`subprocess.Popen`, jamais `shell=True`). A troca de frequência encerra processos anteriores; falhas de remoção/timeout são tratadas e `usb_claim_interface error -6` recebe orientação clara. O número de série pode ser definido em `settings.json`.

PyQt5 foi mantido por ser a arquitetura recomendada e disponível pelo APT no Raspberry Pi OS; não foi feita medição de RAM/CPU no Pi físico, portanto não se afirma que é mais leve que Tkinter/Pygame. O layout evita gestos e controles pequenos. O backend e scanner são independentes da UI para testes e futura substituição.

## Limitações reais

- Favoritos e scanner ainda não estão implementados na interface; seus botões informam essa limitação sem sugerir que há recepção/varredura em andamento.
- `rtl_fm` AM/FM/WFM é o backend implementado; USB/LSB, radioamador, CB/PX e presets regulatórios não estão implementados.
- 27 MHz pode ser teoricamente alcançável, mas qualidade depende de PPM, ruído do Pi, filtro e antena de 11 m; não há promessa de desempenho. Veja [EXPANSOES-FUTURAS.md](docs/EXPANSOES-FUTURAS.md).
- O desligamento chama `systemctl poweroff`; a política sudo/systemd do serviço deve ser verificada no Pi.

## Desenvolvimento e testes

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q app
shellcheck scripts/*.sh radioctl
bash scripts/install.sh --dry-run --non-interactive
```

O último comando deve recusar corretamente esta máquina de desenvolvimento se ela não for Raspberry Pi OS ARMv7. CI executa testes, compilação e ShellCheck. Consulte [HARDWARE.md](docs/HARDWARE.md) e [INSTALACAO.md](docs/INSTALACAO.md) antes do primeiro teste no equipamento.

## Estrutura

```text
app/          interface, backend, scanner, áudio, GPIO e diagnóstico
config/       exemplos de configurações e presets JSON
scripts/      instalação, atualização, desinstalação, diagnóstico e backup
systemd/      serviço de inicialização
docs/         instalação, hardware, recuperação e expansões
```

Licença: [MIT](LICENSE).
