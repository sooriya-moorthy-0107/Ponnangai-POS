# STANDARD OPERATING PROCEDURE (SOP)
## Ponnangai POS — Staff Operations Manual

**Ponnangai Enterprises**
_Version: 1.0 | Last Updated: 26 July 2026_
_Classification: INTERNAL USE ONLY — CONFIDENTIAL_

---

## TABLE OF CONTENTS

1. [Introduction](#1-introduction)
2. [System Overview](#2-system-overview)
3. [Logging In](#3-logging-in)
4. [Shopkeeper Operations](#4-shopkeeper-operations)
5. [Factory Operations](#5-factory-operations)
6. [Manager & Admin Operations](#6-manager--admin-operations)
7. [Receipt & Printing Guide](#7-receipt--printing-guide)
8. [Inventory Management](#8-inventory-management)
9. [Reporting & Analytics](#9-reporting--analytics)
10. [Cash Management](#10-cash-management)
11. [Troubleshooting](#11-troubleshooting)
12. [Security Best Practices](#12-security-best-practices)
13. [Emergency Procedures](#13-emergency-procedures)

---

## 1. INTRODUCTION

### 1.1 Purpose

This Standard Operating Procedure (SOP) provides step-by-step instructions for all staff members on how to use the **Ponnangai POS (Point of Sale)** system for daily business operations. Every employee with POS access must read and understand this manual before operating the system.

### 1.2 Scope

This SOP covers:
- Processing retail sales and billing
- Managing inventory and stock
- Printing thermal receipts
- Generating sales reports
- Managing cash transactions
- User account administration

### 1.3 Roles and Access Levels

| Role | Dashboard | Typical Staff |
|---|---|---|
| **Shopkeeper** | `/shop` — Sales & Billing Interface | Retail shop operators |
| **Factory** | `/factory` — Factory Sales Interface | Factory floor staff |
| **Manager** | `/admin` — Admin Panel (limited) | Shop managers, supervisors |
| **Admin** | `/admin` — Admin Panel (full access) | System administrator |
| **Owner** | `/admin` — Admin Panel (unrestricted) | Business proprietor |

---

## 2. SYSTEM OVERVIEW

### 2.1 Technology

The POS system is a web-based application accessible through any modern web browser (Chrome, Firefox, Edge, Safari). No software installation is required.

### 2.2 Access URL

| Environment | URL |
|---|---|
| **Production** | `https://[your-domain.com]` |
| **Local Development** | `http://localhost:8000` |

### 2.3 System Architecture

```
Browser (Chrome/Firefox)
    ↕ HTTPS
Nginx Reverse Proxy
    ↕
FastAPI Application Server (Uvicorn)
    ↕
PostgreSQL Database
```

---

## 3. LOGGING IN

### Step-by-Step:

1. Open your web browser and navigate to the POS URL.
2. You will be redirected to the **Login Page** (`/login`).
3. Enter your **username** (as assigned by your Admin/Manager).
4. Enter your **password** (case-sensitive).
5. Click **"Login"**.
6. You will be automatically redirected to your role-specific dashboard:
   - **Shopkeeper** → `/shop`
   - **Factory** → `/factory`
   - **Admin / Manager / Owner** → `/admin`

### Important Login Rules:

- ❌ **Never share** your username or password with anyone.
- ❌ **Never write down** your password on paper or sticky notes near the workstation.
- ✅ If you forget your password, contact the **Admin** to reset it.
- ✅ Always **log out** when stepping away from the terminal.

### Logging Out:

Click the **Logout** button (or navigate to `/logout`). Your session will be cleared and you'll be redirected to the login page.

---

## 4. SHOPKEEPER OPERATIONS

### 4.1 The Shop Dashboard (`/shop`)

Upon logging in as a Shopkeeper, you'll see:
- **Product grid** with all your assigned products, images, prices, and stock levels
- **Cart/billing panel** for building the current bill
- **Bill history sidebar** for viewing recent transactions

### 4.2 Processing a Sale

#### Step 1: Add Items to Cart

1. Browse your product grid.
2. **Tap/Click** on a product tile to add it to the cart.
3. The item will appear in the **billing panel** on the right/bottom.
4. Adjust the **quantity** as needed:
   - For **solid products** (Pcs): Use whole numbers (1, 2, 3...)
   - For **liquid products** (Liters): You can enter decimal quantities (0.5, 1.5, 2.0...)

#### Step 2: Select Packaging Type (Liquid Products)

For liquid products, select the packaging type:
- **Loose** — sold by volume (liters)
- **Bottle** — sold in pre-packaged bottles
- If "Bottle" is selected, choose the **bottle type** (e.g., "Pharma Bottle", "Lotus Bottle")
- Enter the **bottle count**

#### Step 3: Apply Discount (If Applicable)

1. Enter the **discount amount** (in Rupees, not percentage) in the discount field.
2. The total will recalculate automatically.
3. Discounts must be approved by the Manager/Admin for amounts above the shop's threshold.

#### Step 4: Select Payment Mode

Choose the payment method:
- **Cash**
- **UPI**
- **Card** (if applicable)

#### Step 5: Submit the Bill

1. Review all items, quantities, and the final amount.
2. Click **"Create Bill"** or the equivalent submit button.
3. The system will:
   - Validate stock availability
   - Deduct stock from inventory
   - Create a bill record in the database
   - Generate a receipt

#### Step 6: Print the Receipt

- You'll be redirected to the **Receipt Page** (`/receipt/{bill_id}`).
- Choose your printing method:
  - **Browser Print** (Ctrl+P / Cmd+P)
  - **Bluetooth Direct Print** (for thermal printers)
  - See [Section 7](#7-receipt--printing-guide) for detailed printing instructions.

### 4.3 Viewing Bill History

1. Open the **Bill History** sidebar panel.
2. View the last 20 bills with details:
   - Bill number
   - Date and time
   - Items, quantities, prices
   - Payment mode
   - Total amount
   - Cancelled status (if voided)

### 4.4 Voiding / Reverting a Bill

> ⚠️ **Use with caution.** Voiding a bill is a serious action.

1. Find the bill in the **Bill History** sidebar.
2. Click the **"Revert/Void"** button on the specific bill.
3. Confirm the action when prompted.
4. The system will:
   - Mark the bill as **"Cancelled"**
   - **Restore** all stock that was deducted
   - The bill items will be loaded back into the cart for correction

**When to void a bill:**
- Customer immediately requests correction (wrong product, wrong quantity)
- Billing error discovered before the customer leaves
- Accidental duplicate bill creation

**Do NOT void a bill:**
- For returns processed hours/days later (contact Manager)
- To manipulate sales data

---

## 5. FACTORY OPERATIONS

### 5.1 Factory Dashboard (`/factory`)

The Factory interface is similar to the Shop interface but with key differences:
- **No stock deduction**: Factory sales do not deduct from inventory.
- **Bottle-focused workflow**: Optimised for packaging types (1L, 5L, 1/2L bottles).
- **Bottle count tracking**: Tracks physical bottle counts for each sale.

### 5.2 Processing a Factory Sale

Follow the same steps as Shopkeeper Operations (Section 4.2), with these differences:
- Select the appropriate **packaging type** and **bottle type** for each item.
- Enter the **bottle count** accurately — this is tracked in reports.
- Stock is **NOT automatically deducted** for Factory role.

---

## 6. MANAGER & ADMIN OPERATIONS

### 6.1 Admin Dashboard (`/admin`)

The Admin Panel provides:
- **User Management**: Add, edit, delete users and assign roles
- **Product Management**: Add, edit, delete products; bulk upload via CSV
- **Inventory Management**: View and update stock levels; bulk upload via CSV
- **Sales Reports**: Generate daily, weekly, and custom date-range reports
- **Analytics**: Real-time revenue dashboard per shop/factory
- **Cash Management**: Track Cash IN/OUT transactions

### 6.2 User Management

#### Adding a New User

1. Navigate to the **User Management** section.
2. Click **"Add User"**.
3. Enter:
   - **Username** (must be unique)
   - **Password** (strong, at least 8 characters)
   - **Role**: Shopkeeper, Factory, Manager, Admin, or Owner
4. Click **"Create"**.

> 📌 **Managers** can only create **Shopkeeper** accounts. Only **Admin/Owner** can create higher-privilege accounts.

#### Editing a User

1. Find the user in the user list.
2. Click **"Edit"**.
3. Modify the **username** or **role**.
4. Click **"Save"**.

#### Deleting a User

- **Soft Delete** (Admin/Owner): Archives the user. Their data is preserved but they can no longer log in. All their products are hidden and stock is zeroed.
- **Hard Delete** (Admin only): Permanently removes the user and ALL their associated data (bills, products, inventory, cash transactions). **This action is irreversible.**

#### Resetting Passwords

Only **Admin** can reset passwords:
1. Select the user.
2. Click **"Change Password"**.
3. Enter the new password.
4. Click **"Update"**.

### 6.3 Product Management

#### Adding a Single Product

1. Navigate to **Product Management**.
2. Click **"Add Product"**.
3. Enter:
   - **Product Name**
   - **Price** (₹)
   - **Initial Stock** quantity
   - **Product Type**: Solid or Liquid
   - **Unit**: Pcs, Liters, etc.
   - **Assigned Shopkeeper** (which shop this product belongs to)
4. Click **"Add"**.

#### Bulk Uploading Products (CSV)

1. Click **"Download Template"** to get the CSV format.
2. Fill in the CSV with product data:
   ```
   Product Name, Price, Initial Stock, Product Type, Unit, Image Name
   Soft Broom, 120.00, 20, solid, Pcs, Soft Broom Front
   Mop, 200.00, 20, solid, Pcs, mop pic
   Clothwash, 80.00, 0, liquid, Liters, clothwash
   ```
3. Select the **target shopkeeper**.
4. Upload the CSV file.
5. The system will add new products or update existing ones (matched by name).

#### Editing a Product

1. Find the product in the product list.
2. Click **"Edit"**.
3. Modify name, price, rate quantity, stock, or upload a new product photo.
4. Click **"Save"**.

#### Deleting a Product

Click **"Delete"** on the product. This performs a **soft delete** — the product is hidden but preserved in the database for historical bill records.

### 6.4 Uploading Product Photos

1. Click the **camera/upload icon** on the product tile.
2. Select an image file (JPEG, PNG).
3. The image will be uploaded and displayed on the product tile.
4. Only **image files** are accepted (validated by MIME type).

---

## 7. RECEIPT & PRINTING GUIDE

### 7.1 Receipt Layout

Each receipt displays:
- **Header**: "Ponnangai Enterprises" / "Housekeeping Products"
- **Bill Metadata**: Bill #, Date/Time, Cashier Name, Payment Mode
- **Itemised Table**: Product Name, Rate, Quantity, Amount
- **Summary**: Subtotal, Discount (if any), Round-off, **Total Paid** (₹)
- **Footer**: "Please visit again!"
- **Void Banner** (if applicable): Large red "VOID / CANCELLED RECEIPT" banner

### 7.2 Browser Print (All Users)

1. On the receipt page, click **"Print via Browser Dialog"**.
2. Your browser's print dialog will open.
3. Set the printer to your connected thermal printer (or "Save as PDF" to test).
4. Click **"Print"**.

### 7.3 Bluetooth Direct Print (Thermal Printers)

For wireless Bluetooth thermal printers (e.g., 58mm/80mm):

1. Click **"Connect Printer"**.
2. Your browser will show a Bluetooth device selector.
3. Select your thermal printer from the list.
4. Wait for "Connected" status.
5. (Optional) Click **"Test Slip"** to print a test receipt.
6. Click **"Print via Bluetooth"** to print the receipt directly.

### 7.4 Print Configuration (Admin Only)

Admins can configure:
- **Paper Width**: 58mm (2") Standard or 80mm (3") Wide
- **Font Size**: 9px to 14px
- **Line Spacing**: 1.0 to 1.6
- **Characters per Line**: 24 to 48 (reduce if text gets cut off on narrow paper)
- **Auto-Print on Load**: Enable for automatic printing when the receipt page loads

These settings are saved in **browser Local Storage** and persist across sessions.

---

## 8. INVENTORY MANAGEMENT

### 8.1 Viewing Inventory

1. Navigate to the **Inventory** section in the Admin Panel.
2. Select a **shopkeeper/shop** to view their inventory.
3. Each product will show: Name, Price, Current Stock, Image.

### 8.2 Updating Stock Manually

1. Find the product.
2. Enter the new stock value.
3. Click **"Update"**.

### 8.3 Bulk Inventory Update (CSV)

1. Click **"Download Inventory Template"** for the target shop.
2. The CSV will contain:
   ```
   S.No., Product Name, Current Stock, New Stock
   1, Soft Broom, 15,
   2, Hard Broom, 8,
   ```
3. Fill in the **"New Stock"** column with the quantity to **add** to existing stock.
4. Upload the CSV.
5. The system will add the new stock amounts to existing levels.

> ⚠️ **Important**: The "New Stock" value is **additive**. If Current Stock = 10 and you enter New Stock = 5, the result will be 15.

### 8.4 Stock Deduction (Automatic)

Stock is automatically deducted when:
- A **bill is created** for a Shopkeeper (not Factory)
- Stock deduction = quantity sold

Stock is automatically restored when:
- A **bill is voided/reverted**

### 8.5 Low Stock Monitoring

The Admin dashboard displays low-stock warnings. Review regularly and restock before products run out.

---

## 9. REPORTING & ANALYTICS

### 9.1 Daily Sales Report

1. Navigate to **Reports** > **Daily Report**.
2. Select the **shop/shopkeeper**.
3. Set the **date range** (Start Date → End Date).
4. Click **"Generate"**.
5. The report will display:
   - Product-wise sales breakdown (quantity and revenue)
   - Revenue by payment mode (Cash / UPI / Card)
   - Cash IN/OUT transaction summary
   - Total Revenue and Net Cash in Drawer
   - Bottle counts (for Factory)

### 9.2 Exporting Reports (CSV)

1. After generating a report, click **"Export CSV"**.
2. A CSV file will download with the report data.
3. File naming: `Sales_Report_[ShopName]_[StartDate]_to_[EndDate].csv`

### 9.3 Shop Analytics

The analytics dashboard shows:
- **Total Sales Count** and **Total Revenue** for each shop
- **Product breakdown**: Which products are selling the most
- **Today's Summary**: Real-time sales data for the current day

---

## 10. CASH MANAGEMENT

### 10.1 Cash IN Transactions

Record cash received outside of regular sales:
- Cash deposits from the owner
- Petty cash received
- Change floats loaded at the start of day

### 10.2 Cash OUT Transactions

Record cash paid out:
- Business expenses (supplies, repairs)
- Petty cash withdrawals
- Vendor payments made from the cash drawer

### 10.3 Recording a Transaction

1. Navigate to **Cash Management**.
2. Select the **shop/shopkeeper**.
3. Enter:
   - **Amount** (₹)
   - **Type**: IN or OUT
   - **Description**: Brief note explaining the transaction (e.g., "Morning float", "Purchased cleaning supplies")
4. Click **"Submit"**.

### 10.4 Cash Reconciliation

At the end of each day:
1. Generate the **Daily Report** for the shop.
2. Compare the report's **"Total After Expense (Cash in Drawer)"** with the physical cash count.
3. Report any discrepancies to the Manager/Admin immediately.

---

## 11. TROUBLESHOOTING

| Issue | Solution |
|---|---|
| **Can't log in** | Check username and password (case-sensitive). Contact Admin for password reset. |
| **"Insufficient stock" error** | The product doesn't have enough stock. Contact Manager to update inventory. |
| **Bluetooth printer not found** | Ensure the printer is powered on and in pairing mode. Use Chrome browser (Bluetooth API requires Chrome). |
| **Receipt text getting cut off** | Ask Admin to reduce "Characters per Line" in print settings (try 26–28 for 58mm paper). |
| **Bill not appearing in history** | Refresh the page. If still missing, contact Admin to check database. |
| **"CSRF verification failed"** | Your session may have expired. Log out and log back in. |
| **Product photo not uploading** | Ensure the file is an image (JPEG, PNG). Maximum recommended size: 2MB. |
| **CSV upload failed** | Check that the CSV matches the template format. Ensure it's comma-separated (not semicolon). |
| **Page loading slowly** | Check internet connection. Contact Admin if the server needs restarting. |

---

## 12. SECURITY BEST PRACTICES

### Do's ✅

1. **Always log out** when leaving the workstation unattended.
2. **Use a strong password** (minimum 8 characters, mix of letters and numbers).
3. **Report suspicious activity** immediately to the Admin.
4. **Lock your device** when not in use.
5. **Verify bill amounts** before confirming a sale.
6. **Count cash** at the start and end of each shift.

### Don'ts ❌

1. **Never share** your login credentials with anyone.
2. **Never let customers** see or touch the POS screen.
3. **Never void a bill** without a genuine reason and Manager approval.
4. **Never download** or copy business data to personal devices.
5. **Never use** the POS system for personal tasks.
6. **Never access** another shopkeeper's account or data.
7. **Never take screenshots** or photos of the POS system.

---

## 13. EMERGENCY PROCEDURES

### System Down / Server Unreachable

1. **Do not panic.** Note the time of the outage.
2. **Use manual billing** (pen and paper) until the system is restored.
3. Contact the Admin immediately.
4. Once the system is back, enter the manually recorded bills into the POS.

### Suspected Data Breach

1. **Immediately change your password.**
2. **Log out** of all sessions.
3. **Notify the Admin/Owner** without delay.
4. **Do not delete** any evidence (logs, messages, etc.).

### Hardware Failure (Printer/Device)

1. Try restarting the device.
2. Try a different browser.
3. If using Bluetooth printing, try Browser Print (Ctrl+P) as a fallback.
4. Contact the Admin for technical support.

---

## DOCUMENT CONTROL

| | |
|---|---|
| **Document ID** | SOP-POS-001 |
| **Version** | 1.0 |
| **Author** | _[Insert Author Name]_ |
| **Approved By** | _[Insert Proprietor Name]_ |
| **Classification** | INTERNAL — CONFIDENTIAL |
| **Distribution** | All POS system users |
| **Review Cycle** | Every 6 months or upon major system update |

---

> **ACKNOWLEDGEMENT:** I have read, understood, and agree to follow the Standard Operating Procedure outlined in this document.
>
> | | |
> |---|---|
> | **Employee Signature** | _________________________ |
> | **Employee Name** | _________________________ |
> | **Date** | _________________________ |
