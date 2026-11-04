#!/bin/bash
set -e

echo "Starting deployment..."
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nginx git certbot python3-certbot-nginx postgresql-client libpq-dev

cd /home/ubuntu
if [ ! -d "/home/ubuntu/Ponnangai-POS" ]; then
    git clone https://github.com/sooriya-moorthy-0107/Ponnangai-POS.git /home/ubuntu/Ponnangai-POS
else
    cd /home/ubuntu/Ponnangai-POS
    git pull origin production
fi

cd /home/ubuntu/Ponnangai-POS
python3 -m venv venv
./venv/bin/pip install wheel
./venv/bin/pip install -r requirements.txt

# Note: Ensure .env is populated with Supabase DATABASE_URL, SECRET_KEY, and PRODUCTION=True.
# You can also run `./venv/bin/python scripts/init_supabase.py` to initialize tables and admin.

cat << 'EOF' | sudo tee /etc/systemd/system/ponnangai-pos.service
[Unit]
Description=Uvicorn instance to serve Ponnangai POS
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/Ponnangai-POS
Environment="PATH=/home/ubuntu/Ponnangai-POS/venv/bin"
EnvironmentFile=/home/ubuntu/Ponnangai-POS/.env
ExecStart=/home/ubuntu/Ponnangai-POS/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl restart ponnangai-pos
sudo systemctl enable ponnangai-pos

cat << 'EOF' | sudo tee /etc/nginx/sites-available/ponnangai-pos
server {
    listen 80;
    server_name pos.ponnangai.com www.pos.ponnangai.com;

    # Force HTTPS redirect for all incoming HTTP traffic
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name pos.ponnangai.com www.pos.ponnangai.com;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # HSTS & Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;

    # File upload limit
    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/ponnangai-pos /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Obtain and renew Let's Encrypt certificates automatically
echo "Configuring SSL with Certbot..."
sudo certbot --nginx -d pos.ponnangai.com -d www.pos.ponnangai.com --non-interactive --agree-tos --redirect -m admin@ponnangai.com || echo "Notice: Certbot configuration will activate once domain DNS resolves to this server."

sudo systemctl restart nginx

echo "Deployment script finished."
