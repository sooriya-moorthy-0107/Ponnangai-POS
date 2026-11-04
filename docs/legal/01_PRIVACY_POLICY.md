# PRIVACY POLICY

**Ponnangai Enterprises**
_Last Updated: 26 July 2026_

---

This Privacy Policy describes how **Ponnangai Enterprises** ("we", "us", "our"), a sole proprietorship / business entity based in Chennai, Tamil Nadu, India, collects, uses, stores, and protects your personal information when you:

1. Visit our website at **[ponnangaienterprises.com]** (the "Website");
2. Interact with our retail shops or factory outlets;
3. Submit an inquiry through our Contact page, Enquiry Modal, or Product Quote request;
4. Conduct transactions at any Ponnangai point-of-sale ("POS") terminal.

This policy is published in compliance with **Section 43A of the Information Technology Act, 2000** and **Rule 4 of the Information Technology (Reasonable Security Practices and Procedures and Sensitive Personal Data or Information) Rules, 2011** ("IT Rules 2011").

---

## 1. INFORMATION WE COLLECT

### 1.1 Information You Provide to Us Directly

| Data Type | Where Collected | Purpose |
|---|---|---|
| **Full Name** | Contact form, Enquiry Modal, Quote Request cart | To identify you and personalise communication |
| **Phone / WhatsApp Number** | Contact form, Enquiry Modal, Quote Request cart | To respond to your inquiry via WhatsApp or phone call |
| **Email Address** (optional) | Contact form, Enquiry Modal | To send follow-up correspondence if provided |
| **Inquiry Message / Product Interest** | Contact form, Enquiry Modal, Product Quote Request | To understand your requirements and provide accurate pricing |

### 1.2 Information Collected During POS Transactions (In-Store)

| Data Type | Purpose |
|---|---|
| **Bill Number, Timestamp, Cashier Name** | Transaction record-keeping and receipt generation |
| **Items Purchased, Quantities, Prices** | Billing, inventory management, and sales reporting |
| **Payment Mode** (Cash / UPI / Card) | Payment reconciliation |
| **Discount Applied, Round-Off Amount** | Accurate financial record-keeping |

> **Note:** Our POS system does **NOT** collect customer names, phone numbers, email addresses, or any personal identifiers during in-store transactions. Receipts are anonymous and linked only to the cashier's session.

### 1.3 Automatically Collected Technical Data (Website)

When you visit the Website, standard web server logs may collect:
- IP address
- Browser type and version
- Device type (mobile, desktop, tablet)
- Pages visited and time spent
- Referring URL

We do **not** use third-party analytics trackers, advertising pixels, or cookie-based profiling on the Website at this time. The Website uses **browser Local Storage** solely for printer configuration preferences on the POS system.

### 1.4 Third-Party Services

When you submit an inquiry, your data is transmitted to **WhatsApp (Meta Platforms, Inc.)** via the WhatsApp Business API link (`wa.me`). This transmission is governed by WhatsApp's own privacy policy. We do not store your inquiry data on our servers — it is sent directly from your browser to WhatsApp.

---

## 2. HOW WE USE YOUR INFORMATION

We use the information collected for the following purposes:

1. **Responding to Inquiries**: To contact you regarding your product inquiry, bulk pricing request, or customer support query.
2. **Order Fulfilment**: To process and fulfil wholesale or retail orders.
3. **Internal Business Operations**: To manage inventory, generate sales reports, track cash flow, and perform business analytics through our POS system.
4. **Legal Compliance**: To comply with applicable Indian tax, accounting, and commercial laws.
5. **Communication**: To send you information about products, offers, or business updates — only if you have explicitly consented or initiated the conversation.

We do **NOT**:
- Sell, rent, or trade your personal information to any third party.
- Use your data for automated decision-making or profiling.
- Send unsolicited marketing communications without your prior consent.

---

## 3. DATA STORAGE AND SECURITY

### 3.1 Storage Infrastructure

| System | Database | Hosting |
|---|---|---|
| POS Application | PostgreSQL 15 (Production) / SQLite (Development) | Self-hosted on Ubuntu server with Nginx reverse proxy |
| Website | No server-side database; static React application | Deployed as a static site |

### 3.2 Security Measures

We implement the following reasonable security practices as mandated under **Rule 8 of the IT Rules, 2011**:

- **Password Hashing**: All POS user passwords are hashed using **bcrypt** (via Passlib) and are never stored in plain text.
- **Session Security**: Server-side session management using **cryptographic signature tokens** (ItsDangerous library) with HTTP-only, `SameSite=Lax` cookies. In production, cookies are marked `Secure` (HTTPS-only).
- **CSRF Protection**: Custom middleware validates `Origin` and `Referer` headers on all state-changing requests (POST, PUT, DELETE, PATCH).
- **Role-Based Access Control (RBAC)**: Five defined roles — Owner, Admin, Manager, Shopkeeper, Factory — each with strictly enforced permission boundaries.
- **HTTPS Encryption**: All production traffic is encrypted using SSL/TLS certificates from Let's Encrypt (Certbot).
- **Soft Deletion**: User and product data is "soft-deleted" (marked as archived) rather than permanently erased, preserving data integrity for auditing.

### 3.3 Data Retention

- **Transaction Data (Bills, Inventory Logs)**: Retained indefinitely for accounting and tax compliance under the Indian Income Tax Act and GST regulations.
- **Inquiry Data**: As inquiries are routed directly to WhatsApp, we retain only WhatsApp chat history as per our normal business communication practices.
- **Archived User Accounts**: Soft-deleted accounts are retained with an "Archived" label. Admin users may permanently purge data upon request.

---

## 4. DATA SHARING AND DISCLOSURE

We may share your information only in the following circumstances:

1. **With your consent**: When you explicitly authorise us to share your details with a specific party.
2. **Service Providers**: With WhatsApp (Meta Platforms) for inquiry routing. No other third-party data processors are currently engaged.
3. **Legal Obligations**: When required by law, court order, or regulatory authority under Indian jurisdiction.
4. **Business Transfers**: In the event of a merger, acquisition, or sale of business assets, your data may be transferred to the successor entity.

---

## 5. YOUR RIGHTS

Under the IT Rules 2011 and applicable Indian law, you have the right to:

1. **Access**: Request a copy of the personal data we hold about you.
2. **Correction**: Request correction of any inaccurate or incomplete personal data.
3. **Withdrawal of Consent**: Withdraw your consent for data processing at any time. This will not affect the lawfulness of processing prior to withdrawal.
4. **Deletion**: Request deletion of your personal data, subject to our legal retention obligations.
5. **Grievance Redressal**: Lodge a complaint with our Grievance Officer (details below).

---

## 6. GRIEVANCE OFFICER

In accordance with **Rule 5(9) of the IT Rules 2011**, the Grievance Officer for Ponnangai Enterprises is:

| | |
|---|---|
| **Name** | _[Insert Grievance Officer Name — Proprietor's name recommended]_ |
| **Designation** | Proprietor / Grievance Officer |
| **Email** | ponnangaienterprises12@gmail.com |
| **Phone** | +91 7092148969 |
| **Address** | 2/1 Muthuamman Kovil Street, Thandhai Periyar Nagar, Aynavaram, Chennai - 600023, Tamil Nadu, India |

Grievances will be acknowledged within **48 hours** and resolved within **30 days** of receipt.

---

## 7. CHILDREN'S PRIVACY

Our Website and services are not directed at individuals under the age of **18 years**. We do not knowingly collect personal information from children. If we become aware that a child has provided personal information, we will take steps to delete it.

---

## 8. CHANGES TO THIS POLICY

We reserve the right to update this Privacy Policy at any time. Any changes will be posted on this page with the updated "Last Updated" date. Continued use of the Website or services after any changes constitutes acceptance of the revised policy.

---

## 9. GOVERNING LAW AND JURISDICTION

This Privacy Policy shall be governed by and construed in accordance with the laws of India. Any disputes arising from this policy shall be subject to the **exclusive jurisdiction of the courts in Chennai, Tamil Nadu, India**.

---

## 10. CONTACT US

For any questions regarding this Privacy Policy, please contact us at:

**Ponnangai Enterprises**
2/1 Muthuamman Kovil Street, Thandhai Periyar Nagar, Aynavaram
Chennai - 600023, Tamil Nadu, India

📧 Email: ponnangaienterprises12@gmail.com
📞 Phone: +91 7092148969 / +91 9360249450
💬 WhatsApp: +91 7092148969
