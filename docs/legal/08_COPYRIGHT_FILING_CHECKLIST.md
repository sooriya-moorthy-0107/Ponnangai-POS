# COPYRIGHT FILING CHECKLIST & GUIDE
## For Ponnangai POS & Website — copyright.gov.in

**Ponnangai Enterprises**
_Reference Document — Prepared: 26 July 2026_

---

## OVERVIEW

This checklist covers everything needed to file copyright applications for:

1. **Ponnangai POS** — Point of Sale & Retail Billing System (Computer Programme / Literary Work)
2. **Ponnangai Enterprises Website** — Corporate Website (Computer Programme + Artistic Work)

Copyright is filed through the **Copyright Office, Government of India** portal at [https://copyright.gov.in](https://copyright.gov.in).

---

## STEP 1: DOCUMENTS TO PREPARE BEFORE FILING

### ☐ NOC / Assignment Deed

- **Document**: [05_NOC_ASSIGNMENT_DEED.md](./05_NOC_ASSIGNMENT_DEED.md)
- Print on **non-judicial stamp paper** (₹100 or as applicable in Tamil Nadu)
- Get it **notarised** by a Notary Public
- Sign by both Author (you) and Assignee (business entity)
- Get **two witnesses** to sign
- Scan and save as **PDF** for online upload

### ☐ Source Code Extracts (Rule 70(5) of Copyright Rules)

You need to prepare **PDFs of source code** for each work:

#### For Ponnangai POS:

| Section | Files to Include |
|---|---|
| **First 10 pages** | Start from `main.py` → `app/core/config.py` → `app/core/security.py` → `app/models/database.py` → `app/models/domain.py` → `app/api/dependencies.py` → `app/api/routes/auth.py` → beginning of `app/api/routes/billing.py` |
| **Last 10 pages** | End of `app/api/routes/reports.py` → `app/api/routes/users.py` → `app/api/routes/admin.py` → `templates/receipt.html` → `static/js/receipt.js` |

#### For Ponnangai Website:

| Section | Files to Include |
|---|---|
| **First 10 pages** | Start from `index.html` → `src/main.jsx` → `src/App.jsx` → `src/index.css` → `src/components/Navbar.jsx` → beginning of `src/components/CinematicLoader.jsx` |
| **Last 10 pages** | End of `src/pages/Products.jsx` → `src/pages/Contact.jsx` → `src/components/Footer.jsx` → `src/components/EnquiryModal.jsx` → `src/components/BrochureFab.jsx` |

**Rules:**
- ❌ **No redaction** — under Rule 70(5), no parts of the code can be blacked out or redacted
- ✅ Print code with **line numbers** and **file path headers**
- ✅ Export to a single **PDF** per work
- ✅ Use monospace font (Consolas, Courier New) at 10–11pt for readability

### ☐ Copies of Artistic / Literary Works

Prepare PDFs or image files of:

| Item | Format |
|---|---|
| **Ponnangai Logo** | PNG/SVG/PDF (from `/public/assets/logo.png` or `/static/images/logo.png`) |
| **Website UI Screenshots** | PNG — Capture Home, About, Products, Contact pages |
| **Product Page Designs** | PNG — Show product grid, variant carousel, modals |
| **POS UI Screenshots** | PNG — Capture Login, Shop view, Admin panel, Receipt page |
| **Receipt Design** | PNG/PDF — Sample thermal receipt layout |
| **Brochure PDF** | From `/public/assets/ponnangai_brochure.pdf` |
| **Website Text Content** | PDF — Copy of all descriptive text (taglines, product descriptions, about page content) |

### ☐ Form XIV

- Generated **automatically** when you file on [copyright.gov.in](https://copyright.gov.in)
- Fill in:
  - **Category**: Computer Programme (for POS) / Computer Programme + Artistic Work (for Website)
  - **Title**: "Ponnangai POS — Point of Sale & Retail Billing System" / "Ponnangai Enterprises Website"
  - **Author**: Your full legal name
  - **Claimant/Owner**: Ponnangai Enterprises (attach NOC as proof of assignment)
  - **Date of Creation**: First date of development
  - **Date of First Publication**: Date of first deployment (or mark as "Unpublished")
  - **Country of Origin**: India

---

## STEP 2: FILE ON THE PORTAL

1. **Create an account** at [https://copyright.gov.in](https://copyright.gov.in)
2. Select **"New Application"**
3. Choose **Category**: "Literary Work" (Computer Programme falls under Literary Work)
4. Fill in **Form XIV** with all required details
5. Upload:
   - Source code extracts (PDF)
   - NOC / Assignment Deed (PDF)
   - Artistic works / screenshots (PDF/PNG)
6. Pay the **filing fee**:
   - Software/Literary Work: ₹500 per work (as of 2026; verify current fee)
   - If filing as a business entity, additional documentation may be required
7. Submit the application

---

## STEP 3: POST-FILING

| Stage | Timeline | Action Required |
|---|---|---|
| **Diary Number issued** | Immediately | Save this number for tracking |
| **Mandatory Waiting Period** | 30 days from filing | Any objections can be raised during this period |
| **Examination** | After 30-day waiting | Copyright Office examiner reviews your application |
| **Discrepancy Letter** (if any) | Varies | Respond within the stipulated time |
| **Registration Certificate** | 6–12 months (typical) | Certificate issued and mailed / available on portal |

---

## FILING FEE SUMMARY (Approximate — Verify Current Rates)

| Work | Category | Fee |
|---|---|---|
| Ponnangai POS | Literary Work (Computer Programme) | ~₹500 |
| Ponnangai Website | Literary Work + Artistic Work | ~₹500 each |
| **Total** | | **~₹1,000 – ₹1,500** |

> Fees are subject to change. Check the latest schedule at [copyright.gov.in](https://copyright.gov.in).

---

## IMPORTANT LEGAL REFERENCES

| Reference | Description |
|---|---|
| **Section 2(o)** of Copyright Act, 1957 | Definition of "Literary Work" — includes computer programmes |
| **Section 2(c)** of Copyright Act, 1957 | Definition of "Artistic Work" — includes designs, logos |
| **Section 14** of Copyright Act, 1957 | Rights comprised in copyright |
| **Section 18** of Copyright Act, 1957 | Assignment of copyright |
| **Section 19** of Copyright Act, 1957 | Mode of assignment (must be in writing, signed) |
| **Section 22-23** of Copyright Act, 1957 | Term of copyright (lifetime + 60 years) |
| **Section 57** of Copyright Act, 1957 | Author's special rights (moral rights / right of paternity) |
| **Rule 70(5)** of Copyright Rules, 2013 | Source code submission requirements (first 10 + last 10 pages, no redaction) |
| **Form XIV** of Copyright Rules | Application form for copyright registration |

---

## NOTES

> ⚠️ **Disclaimer**: This checklist is prepared as a general guide based on publicly available information about Indian copyright law. It does **not** constitute legal advice. We recommend consulting a qualified Intellectual Property (IP) attorney before filing, especially for:
> - Determining whether to file the POS and Website as separate works or a combined work
> - Structuring the NOC/Assignment Deed for maximum legal protection
> - Handling any third-party open-source license compliance issues (the POS uses FastAPI, SQLAlchemy, etc. under permissive MIT/BSD licenses)
