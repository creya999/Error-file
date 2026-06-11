# ADBN Instant Card System

**Agricultural Development Bank Nepal – Head Office Card Operations**

A web-based Instant Card Request Management System built with Python (Flask).

---

## Features

| Feature | Details |
|---|---|
| Branch Login | Login with Staff ID or Username |
| Maker → Checker → Admin | Three-step approval workflow |
| Partial Approval | Admin can approve a lower quantity than requested |
| Dispatch Tracking | Admin marks requests as dispatched with courier details |
| Receipt Confirmation | Branch confirms receipt; admin notified via bell icon |
| Card Sales Tracking | Branch records cards sold and remaining stock |
| User Management | Admin adds/activates/deactivates/resets passwords |
| PDF & Excel Export | Export card request lists |
| Change Password | All users can change their own password |

---

## User Roles

| Role | Who | What they can do |
|---|---|---|
| `maker` | Branch staff | Submit card requests |
| `checker` | Branch supervisor | Approve or reject requests before Admin sees them |
| `admin` | Head Office | Final approval, dispatch, user management |

> A checker **cannot** review their own requests.

---

## Card Request Lifecycle

```
Maker submits
      │
      ▼
 [Checker reviews]
      │
 ┌────┴────┐
 ▼         ▼
Approved  Rejected ── closed
 │
 ▼
[Admin reviews]
 │
 ┌────┴────┐
 ▼         ▼
Approved  Rejected
 │
 ▼
[Dispatched] ── Admin adds courier details
 │
 ▼
[Received] ── Branch confirms → Admin notified
 │
 ▼
[Sales Recorded] ── Branch logs cards sold / remaining
```

---

## Prerequisites

### Windows (Production)

Install all of the following **before** running `install.bat`:

| # | Software | Download | Notes |
|---|---|---|---|
| 1 | **Python 3.10 – 3.12** | https://www.python.org/downloads/ | ✅ Check **"Add Python to PATH"** during install. Avoid 3.13+. |
| 2 | **SQL Server Express** | https://www.microsoft.com/en-us/sql-server/sql-server-downloads | Free edition |
| 3 | **SSMS** | https://aka.ms/ssmsfullsetup | To manage the database |
| 4 | **ODBC Driver 17 for SQL Server** | https://aka.ms/odbc17 | Required for Python ↔ SQL Server |
| 5 | **Microsoft C++ Build Tools** | https://visualstudio.microsoft.com/visual-cpp-build-tools/ | Required to build `pyodbc`. Select **"Desktop development with C++"** |

> **Python not in PATH?** Run `add_python_to_path.bat` included in this project, then reopen Command Prompt.

### Mac / Linux (Local Development)

- Python 3.10+ (`brew install python` on Mac)
- No SQL Server or ODBC driver needed — uses SQLite automatically

---

## Windows Installation

### Step 1 — Enable TCP/IP in SQL Server

By default SQL Server blocks TCP connections. Enable it:

1. Open **SQL Server Configuration Manager**
   (search in Start menu, or press `Win+R` → `SQLServerManager15.msc`)
2. Expand **SQL Server Network Configuration**
3. Click **Protocols for MSSQLSERVER** → right-click **TCP/IP** → **Enable**
4. Go to **SQL Server Services** → right-click **SQL Server** → **Restart**

Verify it works:
```bat
sqlcmd -S localhost -U sa -Q "SELECT @@VERSION"
```

> **Named instance?** (e.g. `localhost\SHREYA`) — also make sure **SQL Server Browser** is Running in `services.msc`. Leave `DB_PORT` blank in `.env`.

---

### Step 2 — Create the Database

Open **SSMS** and run:

```sql
CREATE DATABASE adbn_instant_card;
```

---

### Step 3 — Configure `.env`

Copy `.env.example` to `.env` and fill in your details:

```
USE_SQLITE=false

DB_SERVER=localhost
DB_PORT=
DB_NAME=adbn_instant_card
DB_USER=sa
DB_PASSWORD=YourSQLServerPassword

# Generate with: venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=paste-a-long-random-key-here

APP_HOST=127.0.0.1
APP_PORT=5000
APP_THREADS=4
```

---

### Step 4 — Run the Installer

Double-click **`install.bat`**. It will:

1. Detect Python (`python` or `py`)
2. Check ODBC Driver 17
3. Create a virtual environment (`venv\`)
4. Install all packages from `requirements.txt`
5. Open `.env` in Notepad if it doesn't exist
6. Run `migrate.py` — creates/updates all database tables
7. Run `fix_roles.py` — fixes legacy data (safe on fresh installs)
8. Import all 285 branches from `branches.json`

> If migration or branch import shows a warning, set up `.env` correctly and re-run `install.bat`.

---

### Step 5 — Start the App

Double-click **`start.bat`**.

Open browser: **http://localhost:5000**

| Field | Value |
|---|---|
| Staff ID | `ADMIN001` |
| Password | `Admin@1234` |

> ⚠️ **Change the admin password immediately** after first login — navbar → **Change Password**.

---

## Local Development (Mac / Linux)

```bash
# Clone and enter project
git clone https://github.com/creya999/Error-file.git
cd Error-file

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies (skip pyodbc and waitress — Windows only)
pip install flask flask-login flask-sqlalchemy flask-wtf wtforms \
    sqlalchemy werkzeug python-dotenv reportlab openpyxl

# Create .env
cp .env.example .env
```

Edit `.env`:
```
USE_SQLITE=true
SECRET_KEY=any-random-string-for-local-dev
```

Run:
```bash
python import_branches.py   # seed branches (first time only)
python app.py               # start dev server
```

Open **http://localhost:5000** — login: `ADMIN001` / `Admin@1234`

---

## Running Scripts Manually (Windows)

Always use the **venv Python**, not the system Python:

```bat
venv\Scripts\python.exe migrate.py
venv\Scripts\python.exe fix_roles.py
venv\Scripts\python.exe import_branches.py
```

Or activate the venv first, then use `python` normally:
```bat
venv\Scripts\activate.bat
python migrate.py
```

---

## Updating an Existing Installation

```bat
:: 1. Pull latest code, then:
venv\Scripts\python.exe migrate.py
venv\Scripts\python.exe fix_roles.py

:: 2. Restart
start.bat
```

Both scripts are safe to run multiple times.

---

## Production Deployment (IIS + VPN)

For all branches to access via browser over the bank's VPN:

```
Branch PC (VPN) → https://adbn-cards.adbn.gov.np
                        │
                  Windows Server (IIS port 443)
                        │  reverse proxy
                  Waitress/Flask (port 5000, internal)
                        │
                  SQL Server
```

**`web.config`** (place in project root for IIS reverse proxy):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <system.webServer>
    <rewrite>
      <rules>
        <rule name="Flask Proxy" stopProcessing="true">
          <match url="(.*)" />
          <action type="Rewrite" url="http://127.0.0.1:5000/{R:1}" />
        </rule>
      </rules>
    </rewrite>
  </system.webServer>
</configuration>
```

Required IIS modules: [URL Rewrite](https://www.iis.net/downloads/microsoft/url-rewrite) + [ARR](https://www.iis.net/downloads/microsoft/application-request-routing)

**Run as Windows Service** (auto-start on reboot) using [NSSM](https://nssm.cc/download):
```bat
nssm install "ADBN Card System" "C:\ADBN\adbn-instant-card\venv\Scripts\python.exe" "C:\ADBN\adbn-instant-card\serve.py"
nssm set "ADBN Card System" AppDirectory "C:\ADBN\adbn-instant-card"
nssm start "ADBN Card System"
```

---

## Project Structure

```
├── app.py                  # Flask app factory
├── config.py               # DB config (SQL Server / SQLite toggle)
├── models.py               # DB models: User, Branch, CardRequest, CardSale
├── migrate.py              # Adds missing columns — safe to re-run
├── fix_roles.py            # Fixes legacy role/status data — safe to re-run
├── import_branches.py      # Seeds 285 branches from branches.json
├── serve.py                # Production entry point (Waitress)
├── install.bat             # Windows one-click installer
├── start.bat               # Windows launcher
├── add_python_to_path.bat  # Fixes Python not in PATH on Windows
├── .env.example            # Environment variable template
├── routes/
│   ├── auth.py             # Login, logout, change password
│   ├── branch.py           # Maker: submit requests, confirm receipt, log sales
│   ├── checker.py          # Checker: review and approve/reject requests
│   └── admin.py            # Admin: approvals, dispatch, exports, user management
├── utils/
│   └── exports.py          # PDF and Excel export
└── templates/
    ├── base.html
    ├── auth/
    ├── branch/
    ├── checker/
    └── admin/
```

---

## Troubleshooting

**`python` / `pip` not recognized in install.bat**
→ Python is not in PATH. Run `add_python_to_path.bat`, then reopen Command Prompt and try again.

**`No module named flask` when running scripts manually**
→ You're using the system Python. Use: `venv\Scripts\python.exe migrate.py`

**`pyodbc` fails to install**
→ Install [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) — select "Desktop development with C++"

**`no such column` crash after update**
→ Run: `venv\Scripts\python.exe migrate.py`

**Admin dashboard shows no requests after upgrade**
→ Run: `venv\Scripts\python.exe fix_roles.py`

**Cannot connect to SQL Server**
→ TCP/IP is disabled. Follow Step 1 to enable it in SQL Server Configuration Manager.

**Named instance fails (e.g. `localhost\SHREYA`)**
→ Start **SQL Server Browser** service in `services.msc`. Leave `DB_PORT` blank in `.env`.

**Branch dropdown is empty**
→ Run: `venv\Scripts\python.exe import_branches.py`

**Port 5000 already in use**
→ Set `APP_PORT=5001` in `.env`, then access http://localhost:5001

**Forgot admin password**
```bat
venv\Scripts\python.exe -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('NewPassword123'))"
```
Then in SSMS:
```sql
UPDATE users SET password_hash = '<output from above>' WHERE staff_id = 'ADMIN001';
```
