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

echo "DATABASE_URL=\"postgresql://postgres:Ponnangai123*@ponnangai-db.ch4gua8mcdeb.ap-south-1.rds.amazonaws.com:5432/postgres\"" > .env

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

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/ponnangai-pos /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo systemctl restart nginx

echo "Deployment script finished."
