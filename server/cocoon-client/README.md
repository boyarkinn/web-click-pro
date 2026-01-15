# Cocoon client (папка для деплоя на VPS)

Эта папка предназначена для копирования на VPS как часть `/opt/web-click-pro/server`.
Внутри лежит конфигурация, TON‑config и шаблон systemd‑сервиса.

## Содержимое
- `client-config.json` — основной конфиг Cocoon‑client (нужные параметры сети и кошелька).
- `mainnet.cocoon.global.config.json` — конфиг сети TON (mainnet).
- `cocoon-client.service` — unit‑файл systemd (копируется в `/etc/systemd/system/`).

## Проверка работы
- `http://<VPS-IP>:8081/stats`
- `http://<VPS-IP>:8081/jsonstats`

## Логи
- stdout: `/var/log/cocoon-client.log`
- stderr: `/var/log/cocoon-client.err.log`

## Примечание
Если меняете путь установки или порт — обновите их в:
- `client-config.json`
- `cocoon-client.service`
