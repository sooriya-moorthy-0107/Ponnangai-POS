# 🛒 Ponnangai POS

A mobile-first, multi-tenant Point of Sale (POS) and retail billing system built with Python, FastAPI, and Vanilla JS. Designed for high-speed, touch-friendly retail operations with robust multi-shop inventory management, factory production tracking, and real-time analytics.

## ✨ Key Features

*   **📱 Mobile-First POS Interface:** A clean, flat UI optimized for fast tapping on mobile devices and tablets, preventing fat-finger errors with custom alignments.
*   **🏭 Factory & Shop Roles:** Differentiates between standard Shopkeepers (who are bound by strict inventory checks) and the Factory role (which tracks unlimited production sales and bottle counts).
*   **🖨️ Thermal Printer Integration:** Receipts are strictly formatted for 58mm Bluetooth/USB thermal printers, with built-in pairing workflows via Web Bluetooth API.
*   **📊 Centralized Admin Dashboard:** Real-time metrics tracking global revenue, shop-specific itemized sales analytics, and low-stock warnings (< 10 units).
*   **📈 Daily Sales Reports:** Detailed daily and custom-range sales reports with CSV export capabilities, tailored specifically for the needs of shops vs. factory output.
*   **🔄 Advanced Returns Workflow:** Built-in "Bill History" sidebar allowing staff to instantly void bills, dynamically restore stock, and track voided receipts.
*   **📦 Bulk Inventory Management:** Managers can download, edit, and upload CSV files to rapidly update thousands of products and stock levels at once.
*   **🔐 Role-Based Access Control (RBAC):** Distinct tiers of access (Shopkeeper, Factory, Manager, Admin, Owner) ensuring secure data management.

## 🛠️ Technology Stack

*   **Backend:** Python 3, FastAPI
*   **Database:** SQLite, SQLAlchemy ORM
*   **Frontend:** Vanilla HTML, CSS, JavaScript
*   **Templating:** Jinja2

## 🚀 Quick Start

1.  **Clone the repository**
    ```bash
    git clone https://github.com/sooriya-moorthy-0107/Ponnangai-POS.git
    cd Ponnangai-POS
    ```

2.  **Start via Docker (Recommended)**
    ```bash
    docker compose up -d --build
    ```
    Alternatively, install via python directly: `pip install -r requirements.txt` and `python main.py`

3.  **Access the Dashboard**
    Open `http://localhost:8000` in your browser.
    *Default Admin Credentials:* `admin` / `admin123`

## 💡 System Workflow

1.  **Admin Setup:** The Admin logs into the dashboard, creates Shopkeeper and Factory accounts, and adds global products to the database.
2.  **Inventory Allocation:** The Manager bulk-uploads CSV files to assign specific stock levels to different shopkeepers.
3.  **Sales Operations:** Shopkeepers and Factory staff log in on their mobile devices, add items to the cart via the touch grid, specify loose vs bottle packaging, and generate 58mm receipts.
4.  **Reporting:** Owners and Admins monitor real-time revenue, export CSV reports, and track empty bottle returns directly from the centralized dashboard.

---
*Developed for Ponnangai Enterprises.*
