#!/bin/bash
# Скрипт автоматического развертывания web-click-pro на VPS

set -e

echo "=== Развертывание web-click-pro на VPS ==="
echo ""

# 1. Установка зависимостей для COCOON
echo "[1/7] Установка зависимостей для COCOON..."
apt update -qq
apt install -y cmake ninja-build curl wget > /dev/null 2>&1
echo "✓ Зависимости установлены"

# 2. Клонирование проекта
echo "[2/7] Клонирование проекта..."
if [ -d "web-click-pro" ]; then
    echo "Проект уже существует, обновляю..."
    cd web-click-pro
    git pull -q
else
    git clone https://github.com/boyarkinn/web-click-pro.git
    cd web-click-pro
fi
echo "✓ Проект загружен"

# 3. Установка зависимостей Python
echo "[3/7] Установка зависимостей Python..."
cd server
pip3 install -q -r requirements.txt
cd ..
echo "✓ Python зависимости установлены"

# 4. Сборка COCOON (займет время)
echo "[4/7] Сборка COCOON (это займет 10-30 минут)..."
cd cocoon
if [ ! -f "build/Release/client-runner" ]; then
    ./scripts/cocoon-launch --just-build
else
    echo "COCOON уже собран, пропускаю..."
fi
cd ..
echo "✓ COCOON собран"

# 5. Создание systemd сервисов
echo "[5/7] Настройка автозапуска..."

# COCOON client service
cat > /etc/systemd/system/cocoon-client.service << 'EOF'
[Unit]
Description=COCOON Client
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/web-click-pro/cocoon
ExecStart=/root/web-click-pro/cocoon/scripts/cocoon-launch scripts/client.conf
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Python backend service
cat > /etc/systemd/system/web-click-backend.service << 'EOF'
[Unit]
Description=Web Click Pro Backend
After=network.target cocoon-client.service
Requires=cocoon-client.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/web-click-pro/server
Environment="PATH=/usr/bin:/usr/local/bin"
Environment="COCOON_BASE_URL=http://localhost:10000"
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
echo "✓ Сервисы созданы"

# 6. Настройка firewall
echo "[6/7] Настройка firewall..."
ufw allow 22/tcp > /dev/null 2>&1
ufw allow 8000/tcp > /dev/null 2>&1
echo "✓ Firewall настроен"

# 7. Итоги
echo "[7/7] Готово!"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "Развертывание завершено!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Следующие шаги:"
echo ""
echo "1. Настройте COCOON конфигурацию:"
echo "   nano /root/web-click-pro/cocoon/client-config.json"
echo "   (добавьте node_wallet_key из convert-seed-to-key.py)"
echo ""
echo "2. Запустите сервисы:"
echo "   systemctl enable cocoon-client"
echo "   systemctl start cocoon-client"
echo "   systemctl enable web-click-backend"
echo "   systemctl start web-click-backend"
echo ""
echo "3. Проверьте статус:"
echo "   systemctl status cocoon-client"
echo "   systemctl status web-click-backend"
echo ""
echo "4. Проверьте логи:"
echo "   journalctl -u cocoon-client -f"
echo "   journalctl -u web-click-backend -f"
echo ""
echo "5. Проверьте API:"
echo "   curl http://localhost:10000/stats  # COCOON"
echo "   curl http://localhost:8000/api/health  # Backend"
echo ""
