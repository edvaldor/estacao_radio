# Problemas
Execute `radioctl doctor` e `radioctl logs`. Se houver `usb_claim_interface error -6`, o kernel DVB pode estar usando o SDR: confirme no diagnóstico antes de criar blacklist, faça backup de qualquer configuração e reinicie. Touch é descoberto por nome ADS7846, não por `eventN`. Sem SDR, inicie com `--demo`; sem GPIO ou touch, a aplicação continua pela interface disponível.
