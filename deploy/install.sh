#!/usr/bin/env bash
# ============================================================
# AI StroiApp Manager — one-command VPS installer
# Usage (as root, on fresh Ubuntu 22.04):
#   bash <(curl -s https://raw.githubusercontent.com/hacho88/stroiapp.ru/master/deploy/install.sh)
# Or after git clone:
#   bash deploy/install.sh
# ============================================================
set -euo pipefail

DOMAIN="ai.stroiapp.ru"
REPO="https://github.com/hacho88/stroiapp.ru.git"
APP_DIR="/var/www/ai-manager"

echo "=== 1/7 System packages ==="
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y python3 python3-venv python3-pip nginx git curl certbot python3-certbot-nginx

echo "=== 2/7 Clone repository ==="
if [ -d "$APP_DIR/repo/.git" ]; then
    cd "$APP_DIR/repo" && git pull --ff-only
else
    mkdir -p "$APP_DIR"
    git clone "$REPO" "$APP_DIR/repo"
fi

echo "=== 3/7 Python venv + dependencies ==="
cd "$APP_DIR/repo/backend"
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

echo "=== 4/7 Environment file ==="
if [ ! -f .env ]; then
    cp .env.example .env
    echo ">>> ВАЖНО: заполните $APP_DIR/repo/backend/.env (токены OpenCart/DeepSeek/Яндекс) и перезапустите сервис"
fi

echo "=== 5/7 systemd service ==="
cp "$APP_DIR/repo/deploy/ai-manager.service" /etc/systemd/system/ai-manager.service
mkdir -p "$APP_DIR/repo/backend/data"
touch /var/log/ai-manager.log /var/log/ai-manager-error.log
chown -R www-data:www-data "$APP_DIR/repo/backend/data" /var/log/ai-manager.log /var/log/ai-manager-error.log
systemctl daemon-reload
systemctl enable ai-manager
systemctl restart ai-manager

echo "=== 6/7 nginx ==="
cp "$APP_DIR/repo/deploy/nginx-ai.stroiapp.ru.conf" /etc/nginx/sites-available/ai.stroiapp.ru
ln -sf /etc/nginx/sites-available/ai.stroiapp.ru /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

echo "=== 7/7 SSL (Let's Encrypt) ==="
echo "Выпускаем SSL для $DOMAIN (нужна рабочая A-запись на этот сервер)..."
certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --register-unsafely-without-email || \
    echo "!!! SSL не выпущен — проверьте DNS A-запись, затем выполните: certbot --nginx -d $DOMAIN"

echo ""
echo "=== ГОТОВО ==="
echo "Проверка: curl http://$DOMAIN/api/health"
echo "Фронтенд: http://$DOMAIN/"
echo "Не забудьте заполнить backend/.env и перезапустить: systemctl restart ai-manager"
