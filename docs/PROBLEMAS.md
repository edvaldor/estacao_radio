# Problemas
## A interface não abriu

A instalação deve ser executada como root: `sudo ./scripts/install.sh`. Ela inicia o serviço ao terminar e o habilita para os próximos boot. O serviço não depende do autologin: ele é iniciado pelo systemd no alvo `multi-user.target`. Verifique o estado e o erro sem perder o diagnóstico:

```bash
radioctl status
radioctl logs
sudo systemctl restart radio-movel-sdr
```

Se a instalação foi feita por uma revisão anterior, que apenas habilitava o serviço, execute o último comando ou reinicie uma vez.

## Outros diagnósticos

Execute `radioctl doctor` e `radioctl logs`. Se houver `usb_claim_interface error -6`, o kernel DVB pode estar usando o SDR: confirme no diagnóstico antes de criar blacklist, faça backup de qualquer configuração e reinicie. Touch é descoberto por nome ADS7846, não por `eventN`. Sem SDR, inicie com `--demo`; sem GPIO ou touch, a aplicação continua pela interface disponível.
