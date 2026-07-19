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

Execute `radioctl doctor` e `radioctl logs`. Se houver `usb_claim_interface error -6`, o kernel DVB pode estar usando o SDR: confirme no diagnóstico antes de criar blacklist, faça backup de qualquer configuração e reinicie. Touch é descoberto por nome ADS7846, não por `eventN`. Sem SDR, inicie com `--demo`; sem GPIO ou touch, a aplicação continua pela interface disponível.
