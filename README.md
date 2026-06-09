# ✨ Ponnangai POS — Modern Point of Sale & Retail Billing System

Ponnangai POS is a high-performance, mobile-first Point of Sale (POS) and retail billing application. Designed for speed, ease of use, and scalability, it features robust multi-role management, instant inventory tracking, bulk data management, and seamless printer integration.

---

## 🌟 Key Features

*   **📱 Mobile-First Interface:** A modern, tactile, and responsive user interface optimized for fast-paced mobile and tablet touch operations.
*   **🔐 Role-Based Access Control (RBAC):** Defined permissions for Owner, Admin, Manager, and Shop/Factory operators to ensure data security.
*   **🖨️ Thermal Printer Integration:** Ready-to-print formatting for 58mm Bluetooth/USB thermal receipt printers via Web Bluetooth API.
*   **📦 Bulk Inventory Management:** Standardized templates for CSV bulk uploads and downloads to quickly update product catalogs and stock levels.
*   **🔄 Advanced Returns & Voids:** Interactive transaction history sidebar allowing staff to void bills, track voided receipts, and automatically restore stock levels.
*   **📊 Business Intelligence:** Centralized analytics dashboard displaying real-time revenue, itemized sales trends, and automated low-stock warnings.

---

## 🛠️ Tech Stack & Architecture

*   **Backend:** Python 3.x, FastAPI (Asynchronous Web Framework)
*   **Frontend:** HTML5, CSS3 (Modern Flat Design), Vanilla ES6 JavaScript, Jinja2 Templates
*   **Database:** PostgreSQL (via SQLAlchemy ORM & Alembic migrations)
*   **Infrastructure:** Nginx (Reverse Proxy), Systemd (Process Supervisor), Let's Encrypt (SSL/TLS Encryption)

---

## 💻 Getting Started

### 1. Local Development (Docker)
The quickest way to spin up the entire application locally:
```bash
# Clone the repository
git clone https://github.com/<your-username>/Ponnangai-POS.git
cd Ponnangai-POS

# Spin up services
docker compose up -d --build
```
The application will be accessible at `http://localhost:8000`.

### 2. Manual Setup
For local development without Docker:
```bash
# Set up a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
python main.py
```

---

## 🌐 Production Deployment

The project includes production-grade configuration files and a deployment helper script ([deploy.sh](file:///d:/Ponnangai/retail%20billing%20software/Ponnangai-POS/deploy.sh)) for Ubuntu servers.

### ⚡ Automated Deployment Setup
For initial server provisioning, you can execute the configuration script on your host machine:
```bash
chmod +x deploy.sh
./deploy.sh
```
This script installs environment dependencies, configures Python venv, establishes Nginx server blocks, setups the application's Systemd service, and wires the environment configurations.

### 🔄 Deploying Updates (Zero-Downtime Pipeline)
To pull your latest changes and restart the application backend without logging in manually, execute this one-liner from your local development environment:

```bash
ssh -i "/path/to/key.pem" ubuntu@<your-server-ip> "cd /home/ubuntu/Ponnangai-POS && git pull origin production && ./venv/bin/pip install -r requirements.txt && sudo systemctl restart ponnangai-pos"
```

### 📋 Diagnostics & Operations
Once deployed, use these standard commands on the server to manage the service lifecycle:

| Action | Command |
| :--- | :--- |
| **Check service status** | `sudo systemctl status ponnangai-pos` |
| **Restart application** | `sudo systemctl restart ponnangai-pos` |
| **View live log stream** | `sudo journalctl -u ponnangai-pos -f` |
| **Restart web server** | `sudo systemctl restart nginx` |

---
*Developed for Ponnangai Enterprises.*
