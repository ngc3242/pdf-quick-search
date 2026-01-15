#!/bin/bash
# PDF Quick Search VPS Setup Script
# Run this script on the VPS server as root

set -e

echo "=== PDF Quick Search VPS Setup ==="

# Variables
APP_DIR="/var/www/pdf-search"
DB_NAME="pdf_search_db"
DB_USER="pdf_search_user"
DB_PASS="CHANGE_THIS_PASSWORD"  # Change this!

# 1. Create application directories
echo "[1/8] Creating application directories..."
mkdir -p $APP_DIR/{backend,frontend/dist,storage}
chown -R www-data:www-data $APP_DIR

# 2. Install system dependencies
echo "[2/8] Installing system dependencies..."
apt update
apt install -y python3.12 python3.12-venv python3-pip nginx postgresql postgresql-contrib

# 3. Setup PostgreSQL
echo "[3/8] Setting up PostgreSQL..."
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';" 2>/dev/null || echo "User already exists"
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" 2>/dev/null || echo "Database already exists"
sudo -u postgres psql -d $DB_NAME -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
echo "PostgreSQL setup complete."

# 4. Create Python virtual environment
echo "[4/8] Creating Python virtual environment..."
cd $APP_DIR/backend
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install gunicorn

# 5. Install Python dependencies
echo "[5/8] Installing Python dependencies..."
pip install -r requirements.txt

# 6. Setup Nginx
echo "[6/8] Configuring Nginx..."
cp /tmp/pdf-search.nginx.conf /etc/nginx/sites-available/pdf-search
ln -sf /etc/nginx/sites-available/pdf-search /etc/nginx/sites-enabled/
nginx -t

# 7. Setup Systemd service
echo "[7/8] Configuring Systemd service..."
cp /tmp/pdf-search.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable pdf-search

# 8. Set permissions
echo "[8/8] Setting permissions..."
chown -R www-data:www-data $APP_DIR
chmod -R 755 $APP_DIR
chmod 700 $APP_DIR/backend/.env 2>/dev/null || true

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Edit /var/www/pdf-search/backend/.env with secure keys"
echo "2. Run database migrations: cd $APP_DIR/backend && source venv/bin/activate && flask db upgrade"
echo "3. Start services: systemctl start pdf-search && systemctl reload nginx"
echo "4. Verify: curl http://localhost:5010/api/health"
echo ""
