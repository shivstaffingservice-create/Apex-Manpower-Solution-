# Apex Manpower Solution website

A responsive starter website based on the supplied Shiv Staff Service project brief, renamed to Apex Manpower Solution.

## Features
- Public landing page and services overview
- Client registration and password login
- Client dashboard to submit and track staffing requests
- Password-protected HR admin dashboard
- HR-only client directory, staff database, request status updates, and basic counts
- Hashed passwords, role-based access checks, CSRF protection, and sitemap/robots endpoints

## Run locally
Requires Python 3.11+.

```bash
python -m venv .venv
# Activate the virtual environment, then:
pip install -r requirements.txt
```

Set environment variables before running. Use a long random SECRET_KEY and a unique admin password (16+ characters recommended).

Linux/macOS:
```bash
export SECRET_KEY='replace-with-a-long-random-secret'
export ADMIN_EMAIL='your-admin-email@example.com'
export ADMIN_PASSWORD='use-a-long-unique-password'
export COOKIE_SECURE=0
python app.py
```

Windows PowerShell:
```powershell
$env:SECRET_KEY='replace-with-a-long-random-secret'
$env:ADMIN_EMAIL='your-admin-email@example.com'
$env:ADMIN_PASSWORD='use-a-long-unique-password'
$env:COOKIE_SECURE='0'
python app.py
```
Open http://127.0.0.1:5000. The HR admin account is created on first run when ADMIN_EMAIL and ADMIN_PASSWORD are set. Never place real passwords in source code.

## Deploy online
This project includes `render.yaml` as a starting point for Render. Set `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `SECRET_KEY`, and `SITE_URL` in the hosting dashboard. Keep HTTPS enabled and `COOKIE_SECURE=1`. The SQLite database must live on persistent storage; for a production business site, managed PostgreSQL is preferable. A temporary filesystem can lose database records on redeploy.

## Google Search
After deployment to a public HTTPS URL/domain:
1. Verify the domain in Google Search Console.
2. Submit `https://YOUR-DOMAIN/sitemap.xml`.
3. Google indexing may take time and is not guaranteed. Hosting the website and getting it indexed by Google are separate steps.

## Before using real business data
This is a starter build, not a fully audited production system. Add backups, rate limiting, password reset and recovery, MFA for HR, audit logs, privacy notice/consent, and a managed database before storing sensitive employee documents or high volumes of personal data. Document upload, invoices/payments, attendance, salary processing, and staff editing/deletion are not included yet.
