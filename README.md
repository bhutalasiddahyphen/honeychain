# 🍯 HoneyChain – Blockchain-Based Honey Traceability System

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-green.svg)](https://palletsprojects.com/p/flask/)
[![Blockchain](https://img.shields.io/badge/Blockchain-SHA--256%20PoW-amber.svg)]()
[![PWA](https://img.shields.io/badge/PWA-Installable%20Web%20App-orange.svg)]()
[![License](https://img.shields.io/badge/License-MIT-purple.svg)]()

> A production-ready, mobile-responsive, blockchain-simulated supply-chain traceability platform for authentic honey provenance. From the mountain apiary to the retail shelf, HoneyChain cryptographically verifies every harvest, laboratory purity assay, packaging run, and retail distribution event.

---

## 📑 Table of Contents

1. [Key Features](#-key-features)
2. [5-Stage Supply Chain Lifecycle](#-5-stage-supply-chain-lifecycle)
3. [Project Structure](#-project-structure)
4. [Local Setup & Running](#-local-setup--running)
5. [Step-by-Step Online Deployment (Render)](#-step-by-step-online-deployment-render)
6. [Configuring Environment Variables](#-configuring-environment-variables)
7. [QR Code Configuration for Mobile Phones](#-qr-code-configuration-for-mobile-phones)
8. [Installing as a Phone App (PWA)](#-installing-as-a-phone-app-pwa)
9. [Hosting Service Realities & Free Tier Limitations](#-hosting-service-realities--free-tier-limitations)
10. [Database Persistence Guide](#-database-persistence-guide)
11. [Cryptographic Proof vs. Chemical Purity](#-cryptographic-proof-vs-chemical-purity)
12. [Security Architecture](#-security-architecture)

---

## 🌟 Key Features

* **Simulated SHA-256 Blockchain:** Cryptographic proof-of-work (PoW) ledger linking every supply-chain stage. Any unauthorized modification to an earlier block invalidates downstream cryptographic hashes immediately.
* **Live Tamper Simulator & Audit Engine:** Admin interactive tool to simulate SQLite unauthorized database edits and demonstrate instant cryptographic alert detection and 1-click ledger restoration.
* **Dynamic Public QR Codes:** Honey jar QR codes encode live, public traceability URLs (`https://your-domain.com/trace/HC-XXXX-XXXX`) instead of `localhost`, allowing any smartphone camera to scan and inspect provenance in real time.
* **Mobile-First Responsive UI:** Designed with 44px+ touch targets, zoom-safe input fields, responsive data tables, sticky bottom navigation for smartphones, and glassmorphic telemetry cards.
* **Progressive Web App (PWA):** Installable on Android (Chrome) and iPhone (Safari) with custom app icons, standalone window mode, and a privacy-conscious Service Worker (`sw.js`).
* **5 Supply Chain Personas & Role-Based Access:** Dedicated dashboards for **Beekeeper**, **Testing Laboratory**, **Bottling/Packager**, **Authorized Retailer**, and **Public Consumer / Lead Auditor**.
* **ISO-17025 Digital Signatures:** Simulates accredited laboratory HMAC-SHA256 digital signing for moisture, purity, and NMR spectrum verification.
* **Audit-Grade PDF Provenance Certificates:** Automated generation of tamper-evident PDF inspection certificates with embedded QR codes.

---

## ⛓️ 5-Stage Supply Chain Lifecycle

| Block | Phase | Responsible Persona | Telemetry & Cryptographic Data |
| :---: | :--- | :--- | :--- |
| **0** | **Genesis Block** | System Consortium | Cryptographic root block (`prev_hash: '0'`). |
| **1** | **Apiary Harvest** | Beekeeper | Floral source, apiary coordinates, comb type, harvest date, cold centrifugation method, batch quantity. |
| **2** | **Lab Quality Assay** | Testing Laboratory | Moisture content, HMF level, NMR profile, purity score %, accredited lab license, HMAC digital signature. |
| **3** | **Bottling & Sealing** | Packager / Facility | Clean room plant, jar format (e.g. 500g amber glass), tamper-evident seal ID, lot number. |
| **4** | **Retail Shelf** | Authorized Seller | Store location, retail license, shelf arrival timestamp, retail price, authenticated retail status. |

---

## 📂 Project Structure

```text
HONEY CHAIN/
├── .env.example              # Production environment variable template (no real secrets)
├── .gitignore                # Protects secrets, local SQLite DB, virtualenvs & caches
├── Procfile                  # Production process definition for Gunicorn WSGI server
├── render.yaml               # Render Infrastructure-as-Code Blueprint configuration
├── requirements.txt          # Python dependencies (Flask, Gunicorn, QRCode, Pillow, etc.)
├── run.bat                   # 1-click Windows local runner
├── share_online.bat          # 1-click Cloudflare/Ngrok tunnel helper for quick mobile testing
├── open_firewall.bat         # Windows Defender Firewall helper for LAN Wi-Fi testing
│
├── app.py                    # Main Flask application (routes, auth, QR generation, PWA endpoints)
├── blockchain.py             # SHA-256 Proof-of-Work blockchain engine & database auditor
├── database.py               # SQLite schema, Werkzeug password hashing, baseline data seeding
├── pdf_generator.py          # ReportLab PDF certificate generator
│
├── static/
│   ├── manifest.json         # Web App Manifest for mobile installation
│   ├── sw.js                 # Production-safe Service Worker (offline fallback, asset cache)
│   ├── style.css             # Mobile-responsive design system, dark mode & touch utilities
│   ├── icons/                # PWA high-res icons (192px, 512px, maskable, apple-touch-icon)
│   │   ├── favicon.png
│   │   ├── icon-192.png
│   │   ├── icon-512.png
│   │   ├── icon-maskable.png
│   │   └── apple-touch-icon.png
│   └── qrcodes/              # Auto-generated batch traceability QR code PNGs
│
├── templates/
│   ├── index.html            # Unified Master Portal (5 tabs, responsive UI, PWA modal, tamper banner)
│   ├── login.html            # Dedicated login view
│   ├── register.html         # Batch registration view
│   ├── trace.html            # Dedicated traceability inspection view
│   ├── dashboard.html        # Analytics view
│   └── offline.html          # PWA offline fallback screen (explains live verification need)
│
└── instance/
    └── honeychain.db         # Local SQLite database (git-ignored in production)
```

---

## 💻 Local Setup & Running

### 1. Prerequisites
* Python 3.10, 3.11, or 3.12 installed on your machine.
* Git installed.

### 2. Install Dependencies
Open PowerShell or Command Prompt in the project folder and run:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Launch Development Server
```bash
python app.py
```
Open your browser to: `http://127.0.0.1:5000`

---

## 🚀 Step-by-Step Online Deployment (Render)

We recommend [Render](https://render.com) because it offers a native Python runtime, automatic HTTPS, GitHub integration, and a free tier suitable for student projects.

### Step 1: Create a GitHub Repository

1. Log into your GitHub account at [github.com](https://github.com).
2. Click **New Repository** (green button).
3. Name your repository (e.g., `honeychain`).
4. Set visibility to **Public** or **Private**.
5. Do **not** initialize with a README, .gitignore, or license (these already exist in the project).
6. Click **Create repository**.

### Step 2: Push Your Project to GitHub

In your project directory on your computer, run:
```bash
git init
git add .
git commit -m "Initial commit of HoneyChain production ready system"
git branch -M main
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/honeychain.git
git push -u origin main
```
*(Replace `<YOUR_GITHUB_USERNAME>` with your real GitHub username).*

### Step 3: Connect to Render

1. Go to [dashboard.render.com](https://dashboard.render.com) and create an account (you can sign in with your GitHub account).
2. Click **New +** in the top navigation and select **Web Service**.
3. Choose **Build and deploy from a Git repository**.
4. Connect your GitHub account and select your `honeychain` repository.
5. Fill in the deployment settings:
   * **Name:** `honeychain` (or any unique name you prefer)
   * **Region:** Frankfurt (EU) or Oregon (US)
   * **Branch:** `main`
   * **Root Directory:** *(leave blank)*
   * **Runtime:** `Python 3`
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`
   * **Instance Type:** `Free`

### Step 4: Configure Environment Variables

Scroll down to the **Environment Variables** section on Render and click **Add Environment Variable**:

| Key | Value | Purpose |
| :--- | :--- | :--- |
| `SECRET_KEY` | *(Click "Generate" or paste a random 64-char hex string)* | Signs Flask session cookies securely |
| `PUBLIC_BASE_URL` | `https://your-service-name.onrender.com` | Base URL used to generate batch QR codes |
| `FLASK_ENV` | `production` | Enforces production cookies & security headers |
| `PYTHON_VERSION` | `3.11.9` | Ensures a consistent Python runtime on Render |

> ⚠️ **Important:** When you first create the service, Render will assign your permanent URL (e.g. `https://honeychain-xyz.onrender.com`). Once Render displays this URL, set `PUBLIC_BASE_URL` to that exact address (without a trailing slash) and click **Save Changes**.

### Step 5: Deploy

Click **Create Web Service**. Render will install dependencies, launch Gunicorn, provision a free SSL/HTTPS certificate, and make your site publicly accessible.

---

## 📱 QR Code Configuration for Mobile Phones

In development, QR codes often point to `http://127.0.0.1:5000`, which fails when scanned by an external phone. HoneyChain solves this:

1. **Automatic Detection:** The application inspects the `PUBLIC_BASE_URL` environment variable.
2. **Reverse Proxy Aware:** If `PUBLIC_BASE_URL` is not set, it reads the incoming `X-Forwarded-Proto` and `Host` headers sent by Render's reverse proxy.
3. **Scannable URLs:** Every batch QR code points to:
   ```text
   https://<your-deployed-service>.onrender.com/trace/HC-2026-9842
   ```
4. When a phone camera scans this QR code, it opens the customer traceability view with complete provenance, lab assays, and cryptographic integrity verification.

---

## 📲 Installing as a Phone App (PWA)

HoneyChain includes a Web App Manifest and Service Worker so users can install it as an app without going through the App Store or Google Play:

### On Android (Google Chrome):
1. Open your public HoneyChain URL in **Google Chrome**.
2. Tap the **Install App** button in the HoneyChain navigation bar, OR:
3. Tap the three dots (⋮) in the top-right corner of Chrome.
4. Tap **Add to Home screen** or **Install app**.
5. HoneyChain will install on your home screen and open in standalone full-screen mode.

### On iPhone / iPad (Apple Safari):
1. Open your public HoneyChain URL in **Apple Safari**.
2. Tap the **Share** button (the square with an arrow pointing upward at the bottom of the screen).
3. Scroll down and tap **Add to Home Screen**.
4. Confirm by tapping **Add** in the top-right corner.
5. The HoneyChain golden honey emblem will appear on your iOS home screen.

---

## ⚠️ Hosting Service Realities & Free Tier Limitations

Please understand how the free hosting tier works so there are no surprises during presentations or grading:

### 1. Inactivity Sleep (Spindown)
* Render's free tier spins down (sleeps) web services after **15 minutes of inactivity**.
* When someone opens the link after it has slept, the server takes **30 to 50 seconds** to start back up ("cold start").
* Once active, subsequent page loads are instantaneous.

### 2. Ephemeral Filesystem (Free Tier)
* On free container hosting, the local filesystem is **ephemeral**. This means whenever your application restarts, redeploys, or wakes from sleep, any changes written to local disk revert to the code in your GitHub repository.
* HoneyChain automatically seeds baseline accounts, test batches, and laboratories on startup if the database is fresh, so your demo will always work.
* If you want newly registered user accounts and batches created on the live site to persist permanently across redeployments, see the [Database Persistence Guide](#-database-persistence-guide) below.

### 3. Continuous 24/7 Availability
* Free tiers do not guarantee 100% continuous uptime.
* For continuous 24/7 availability with zero sleep delays, Render offers paid Web Services starting at $7/month, or you can use external pinging services (e.g. UptimeRobot) to ping your free URL every 10 minutes.

---

## 🗄️ Database Persistence Guide

HoneyChain uses SQLite by default via `database.py`. You have two paths for data persistence:

### Option A: Out-of-the-Box Demo (Free Plan)
* HoneyChain stores SQLite at `instance/honeychain.db`.
* On fresh deployment, `database.init_db()` automatically seeds realistic batches (HC-2026-9842, HC-2026-7215, HC-2026-3108, HC-2026-1045) and role accounts.
* Perfect for college evaluations, presentations, and testing.

### Option B: Persistent Disk on Render (Starter Plan)
1. In your Render Web Service dashboard, go to **Disks**.
2. Click **Add Disk**, name it `honeychain-data`, set Mount Path to `/var/data`.
3. Set environment variable: `DATABASE_PATH=/var/data/honeychain.db`.
4. Now all live user registrations, newly mined blocks, and stage updates persist permanently across redeploys.

---

## 🔬 Cryptographic Proof vs. Chemical Purity

> **Academic Note:** A common misconception in blockchain supply chain projects is that a blockchain "proves" honey is pure. It does not.

* **What the Blockchain Proves:**
  * **Immutability:** Once a record is entered with a valid SHA-256 hash and proof-of-work nonce, no unauthorized party can alter the recorded harvest date, beekeeper identity, or test numbers without breaking the cryptographic chain.
  * **Non-Repudiation:** Digital signatures bind specific inspection results to an accredited laboratory's signing key.
* **What the Laboratory Proves:**
  * **Chemical Authenticity:** Proof of purity comes from actual accredited laboratory assays: Nuclear Magnetic Resonance (NMR) spectroscopy, C3/C4 sugar isotope tests, moisture analysis, and Hydroxymethylfurfural (HMF) levels.
* **The Synergistic Result:** The laboratory establishes scientific truth; the blockchain guarantees that the recorded truth cannot be altered after the fact.

---

## 🔒 Security Architecture

1. **Password Hashing:** Passwords are never stored in plaintext. HoneyChain uses `werkzeug.security.generate_password_hash` with PBKDF2-SHA256 salt iterations.
2. **Session Protection:** Session cookies are configured with `HttpOnly=True` (prevents XSS theft) and `SameSite=Lax` (mitigates CSRF). On production/Render, `Secure=True` is enforced over HTTPS.
3. **Secret Isolation:** Cryptographic secrets and application configuration are managed exclusively through environment variables (`os.environ`). No private keys or passwords are committed to Git.
4. **Service Worker Safety:** The Service Worker (`sw.js`) caches only static assets (CSS, icons) and the offline informational page. It strictly bypasses caching for authentication endpoints, session data, and dynamic API responses.

---

## 👥 Default Demo Credentials

For quick testing and grading, HoneyChain pre-seeds the following verified accounts:

| Role | Username | Password | Organization |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` | HoneyChain Lead Consortium Auditor |
| **Beekeeper** | `beekeeper` | `beekeeper123` | Valais High Meadow Apiary |
| **Laboratory** | `lab` | `lab123` | Swiss Agroscope Quality Lab |
| **Packager** | `packager` | `packager123` | Helvetia Artisan Bottlers |
| **Seller** | `seller` | `seller123` | AlpenGourmet Flagship Boutique |
| **Consumer** | `consumer` | `consumer123` | Public Retail Shopper |

*(You can also use the 1-click Quick Persona switcher in the top navigation bar).*

---

## 📄 License
This project is licensed under the MIT License – free for educational, academic, and evaluation use.
