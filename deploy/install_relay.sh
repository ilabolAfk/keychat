#!/usr/bin/env bash
# Установка и автозапуск KeyChat relay на Raspberry Pi (Raspberry Pi OS).
#
# Запуск:  bash install_relay.sh
# Ожидается запуск из папки deploy/, а relay.py — на уровень выше (../relay.py).

set -euo pipefail

APP_DIR="$(cd .. && pwd)"             # корень проекта (где лежит relay.py)
INSTALL_DIR="${HOME}/keychat-relay"   # куда кладём relay на RPi
SERVICE="keychat-relay.service"

echo "==> Копирую relay.py в ${INSTALL_DIR}"
mkdir -p "${INSTALL_DIR}"
cp "${APP_DIR}/relay.py" "${INSTALL_DIR}/relay.py"

echo "==> Устанавливаю python3-websockets"
python3 -m pip install websockets || sudo apt-get install -y python3-websockets

echo "==> Устанавливаю systemd-сервис"
sudo cp "${SERVICE}" "/etc/systemd/system/${SERVICE}"
# Подменяем путь и пользователя, если нужно (по умолчанию /home/pi).
sudo sed -i "s|/home/pi|${INSTALL_DIR}|g; s|^User=pi$|User=${USER}|g" "/etc/systemd/system/${SERVICE}"

echo "==> Включаю и запускаю сервис"
sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE}"
sudo systemctl restart "${SERVICE}"

sleep 2
echo "==> Статус:"
systemctl --no-pager status "${SERVICE}" || true

echo
echo "Готово. Проверка локально:"
echo "  systemctl status ${SERVICE}"
echo "  journalctl -u ${SERVICE} -f"
echo
echo "Открыть наружу: пробросьте порт 8765 на роутере (TCP) до IP этого устройства,"
echo "либо положите за VPN. Адрес для клиентов — ws://<IP или домен>:8765 (см. RELAY_URL в keychat/network.py)."