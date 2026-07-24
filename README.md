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

## 🛠️ Tech Stack & Technologies Used

### 🐍 Backend & Core Infrastructure
*   **Python (v3.11+)**: Primary backend programming language.
*   **FastAPI**: Asynchronous web framework for high-performance RESTful APIs & server-side rendering.
*   **Uvicorn**: ASGI server implementation for serving the FastAPI application.
*   **Jinja2**: Server-side templating engine for dynamic HTML views.
*   **Python-Dotenv**: Environment variable configuration management (`.env`).

### 🗄️ Database & Data Layer
*   **PostgreSQL (v15)**: Relational database management system for production deployments.
*   **SQLite**: Lightweight database for local development and test automation (`test.db`).
*   **SQLAlchemy**: Object-Relational Mapping (ORM) for data modeling and session management.
*   **psycopg2-binary**: PostgreSQL database adapter for Python.

### 🔐 Security & Authentication
*   **Passlib & Bcrypt**: Password hashing and verification algorithms (`bcrypt==3.2.2`).
*   **ItsDangerous**: Cryptographic signature library for secure session token management.
*   **Role-Based Access Control (RBAC)**: Permission enforcement across Owner, Admin, Manager, Factory, and Shop roles.

### 🎨 Frontend & UI/UX
*   **HTML5 & CSS3**: Modern responsive layout using CSS Grid, Flexbox, Custom Properties (Variables), and Glassmorphism design elements.
*   **Vanilla JavaScript (ES6+)**: Client-side interactive logic with standard Fetch API and DOM manipulation (no heavy frameworks).
*   **SweetAlert2**: Interactive custom notification modals and action confirmation dialogs.

### 🖨️ Hardware & Web APIs
*   **Web Bluetooth API**: Direct browser-to-hardware communication with 58mm/80mm Bluetooth thermal printers.
*   **ESC/POS Command Protocol**: Binary formatting for thermal receipt printing (text alignment, font styling, cutter control).
*   **Web Storage API**: Browser LocalStorage for persisting printer configurations and local app settings.

### 📦 Data Handling & Import/Export
*   **Python-Multipart**: Form data parsing for file uploads (product photos, inventory sheets).
*   **CSV Processing**: Automated bulk catalog import/export processing.

### 🧪 Testing & Quality Assurance
*   **Pytest**: Automated testing framework for backend unit and API endpoint testing.
*   **HTTPX**: Asynchronous HTTP client for testing FastAPI endpoints.

### 🐳 DevOps, Containerization & Server Deployment
*   **Docker & Docker Compose**: Containerized multi-service setup (`python:3.11-slim` app & `postgres:15-alpine` DB).
*   **Nginx**: High-performance reverse proxy web server with HTTP/HTTPS reverse proxy configuration.
*   **Systemd**: Linux process supervisor for background service lifecycle management (`ponnangai-pos.service`).
*   **Certbot & Let's Encrypt**: SSL/TLS encryption for HTTPS.
*   **Bash Scripting**: Automated deployment script ([deploy.sh](file:///d:/Ponnangai/retail%20billing%20software/Ponnangai-POS/deploy.sh)) for Ubuntu servers.


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
