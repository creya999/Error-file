# ADBN Instant Card System

**Agricultural Development Bank Nepal – Head Office Card Operations**

A web-based Instant Card Request Management System built with Python (Flask).
Runs on **Windows with SQL Server** (production) and **Mac/Linux with SQLite** (development/testing).

---

## Features

| Feature | Details |
|---|---|
| Branch Login | Each branch logs in with Staff ID or Username |
| Card Request | Maker submits instant card requests to Head Office |
| Checker Workflow | Checker at the branch reviews and approves/rejects before it reaches Admin |
| Partial Approval | Admin can approve a lower quantity than requested |
| Dispatch Tracking | Admin marks approved requests as dispatched with optional courier details |
| Receipt Confirmation | Branch confirms receipt of cards; admin is notified via bell icon |
| Card Sales Tracking | Branch records how many cards were sold per request |
| Status Tracking | Pending / Approved / Dispatched / Received / Rejected |
| Admin Panel | Head Office admin reviews, approves, rejects, and dispatches requests |
| User Management | Admin can add/activate/deactivate/reset password for branch staff |
| Role Management | Three roles: **maker**, **checker**, **admin** |
| Change Password | All users can change their own password |
| PDF Export | Generate printable card request list PDF |
| Excel Export | Export card request list to Excel |

---

## User Roles

| Role | Who | What they can do |
|---|---|---|
| `maker` | Branch staff | Submit card requests |
| `checker` | Branch supervisor | Review and approve/reject requests before they reach Admin |
| `admin` | Head Office | Final approval, dispatch, user management |

> A checker **cannot** approve their own requests. Once a checker approves a request, it appears in the Admin queue.

---

## Card Request Lifecycle

```
Maker submits request
        │
        ▼
   [Checker Pending]  ←── Checker reviews (same branch)
        │
   ┌────┴────┐
   ▼         ▼
[Checker    [Checker
 Approved]   Rejected]  ←── Request closed, branch notified
   │
   ▼
[Admin Pending]  ←── Admin reviews
   │
   ┌────┴────┐
   ▼         ▼
[Approved] [Rejected]
   │
   ▼
[Dispatched]  ←── Admin marks dispatched (with courier details)
   │
   ▼
[Received]  ←── Branch confirms receipt → Admin notified via bell icon
   │
   ▼
[Sales Recorded]  ←── Branch logs cards sold / remaining
```

---

## Deployment Modes

| Mode | Use case | Server |
|---|---|---|
| `start.bat` (localhost) | Single PC, Head Office only | Waitress on 127.0.0.1:5000 |
| **Domain + VPN** | All branches access via web | Waitress + IIS reverse proxy + VPN |

---

## Domain + VPN Deployment (Recommended for Branch Access)

This is the setup that allows all 285 branches to access the system through a web browser over the bank's VPN.

```
Branch PC (VPN connected)
        │
        │  https://adbn-cards.adbn.gov.np
        ▼
   VPN Server / Firewall
        │
        │  routes to Windows Server IP (internal)
        ▼
   Windows Server (IIS on port 443)
        │
        │  reverse proxy to localhost:5000
        ▼
   Waitress / Flask App (port 5000, internal only)
        │
        ▼
   SQL Server (same machine or another internal server)
```

### What you need

| Item | Notes |
|---|---|
| Windows Server | The machine running this app (can be the same PC as SQL Server) |
| Internal domain or IP | e.g. `adbn-cards.adbn.gov.np` or `192.168.1.100` — assigned by your IT team |
| VPN access for branches | Branches connect to ADBN VPN, then access the domain |
| IIS (Internet Information Services) | Built into Windows Server — used as reverse proxy |
| SSL certificate | Optional but strongly recommended — free from your internal CA or self-signed |

---

### Step A — Configure `.env` for Production

```
USE_SQLITE=false
DB_SERVER=localhost
DB_PORT=1433
DB_NAME=adbn_instant_card
DB_USER=sa
DB_PASSWORD=YourStrongPassword

# Generate this with: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=paste-your-64-character-random-key-here

APP_HOST=127.0.0.1
APP_PORT=5000
APP_THREADS=4
```

---

### Step B — Start the App with Waitress

Double-click **`start.bat`** (or run as a Windows Service — see Step E).

The app now runs on `http://127.0.0.1:5000` — internal only, not directly accessible from outside.

---

### Step C — Set Up IIS as Reverse Proxy

IIS sits in front of the Flask app, handles HTTPS, and forwards requests to port 5000.

**Install IIS and required modules:**

1. Open **Server Manager → Add Roles and Features → Web Server (IIS)**
2. Also install these IIS modules (download from Microsoft):
   - **URL Rewrite** — https://www.iis.net/downloads/microsoft/url-rewrite
   - **Application Request Routing (ARR)** — https://www.iis.net/downloads/microsoft/application-request-routing

**Enable reverse proxy in ARR:**

1. Open **IIS Manager**
2. Click the server name → **Application Request Routing Cache → Server Proxy Settings**
3. Check **Enable proxy** → Apply

**Create a new IIS Site:**

1. IIS Manager → **Sites → Add Website**
   - Site name: `ADBN Card System`
   - Physical path: `C:\ADBN\adbn_instant_card\` (the project folder)
   - Binding: `https`, port `443`, hostname: `adbn-cards.adbn.gov.np`
   - SSL certificate: select your certificate (or self-signed for internal VPN use)

**Add `web.config` to the project folder** (`C:\ADBN\adbn_instant_card\web.config`):

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

Save the file, then restart IIS:
```
iisreset
```

**Test:** Open a browser on the server itself and go to `https://adbn-cards.adbn.gov.np` — you should see the ADBN login page.

---

### Step D — Open Firewall Port (Windows Firewall)

Allow HTTPS (port 443) through Windows Firewall so VPN-connected branch users can reach the server:

1. Open **Windows Defender Firewall → Advanced Settings**
2. **Inbound Rules → New Rule**
   - Rule type: Port
   - Protocol: TCP, port 443
   - Action: Allow the connection
   - Profile: Domain + Private
   - Name: `ADBN Card System HTTPS`

**Do NOT open port 5000** — that stays internal only (Flask/Waitress).

---

### Step E — Run as a Windows Service (Auto-start on reboot)

So the app starts automatically when the server reboots, without anyone needing to double-click `start.bat`:

```bat
:: Download NSSM from https://nssm.cc/download
:: Run this once in Command Prompt as Administrator
nssm install "ADBN Card System" "C:\ADBN\adbn_instant_card\venv\Scripts\python.exe" "C:\ADBN\adbn_instant_card\serve.py"
nssm set "ADBN Card System" AppDirectory "C:\ADBN\adbn_instant_card"
nssm start "ADBN Card System"
```

To stop/restart the service:
```bat
nssm stop "ADBN Card System"
nssm restart "ADBN Card System"
```

To remove the service:
```bat
nssm remove "ADBN Card System" confirm
```

---

### Step F — DNS / VPN Configuration

Ask your IT / Network team to:

1. Create a **DNS A record**: `adbn-cards.adbn.gov.np` → Windows Server's internal IP (e.g. `192.168.1.100`)
2. Ensure VPN routing allows branch clients to reach that IP on port 443

Branch staff then connect to VPN as normal and open:
```
https://adbn-cards.adbn.gov.np
```

That's it — no special software, just a browser.

---

## Windows Installation (Local / Production)

### Step 1 — Install Prerequisites

Install all of the following before proceeding:

| Software | Where to get it | Notes |
|---|---|---|
| Python 3.10 – 3.12 | https://www.python.org/downloads/ | Check **"Add Python to PATH"** during install. Avoid Python 3.13+ for now. |
| SQL Server Express | https://www.microsoft.com/en-us/sql-server/sql-server-downloads | Free edition, sufficient for this system |
| SSMS | https://aka.ms/ssmsfullsetup | Used to manage the database |
| ODBC Driver 17 for SQL Server | https://aka.ms/odbc17 | Required for Python to connect to SQL Server |
| Microsoft C++ Build Tools | https://visualstudio.microsoft.com/visual-cpp-build-tools/ | Required to build `pyodbc` — select **"Desktop development with C++"** |

---

### Step 2 — Enable TCP/IP for SQL Server

By default, SQL Server only accepts local Shared Memory connections. You must enable TCP/IP so the app can connect.

1. Open **SQL Server Configuration Manager**
   - Press `Win + R`, type `SQLServerManager15.msc` (adjust version number if needed), press Enter
   - Or search **"SQL Server Configuration Manager"** in the Start menu
2. Expand **SQL Server Network Configuration**
3. Click **Protocols for MSSQLSERVER** (or your instance name, e.g. `SHREYA`)
4. Right-click **TCP/IP** → **Enable**
5. Go to **SQL Server Services** → right-click **SQL Server (MSSQLSERVER)** → **Restart**

> **Named instance?** If your SQL Server is a named instance (e.g. `DESKTOP-PC\SHREYA`), also make sure **SQL Server Browser** service is Running (`services.msc`).

**Verify TCP/IP is working:**
```bat
sqlcmd -S localhost -U sa -Q "SELECT @@VERSION"
```
If using a named instance:
```bat
sqlcmd -S localhost\YOURINSTANCE -U sa -Q "SELECT @@VERSION"
```
This must succeed before proceeding.

---

### Step 3 — Create the Database

Open **SSMS**, connect to your SQL Server instance, and run:

```sql
CREATE DATABASE adbn_instant_card;
```

---

### Step 4 — Extract the Project

Extract the project ZIP to a folder, e.g.:

```
D:\ADBL INSTANT CARD\adbn-instant-card\
```

---

### Step 5 — Configure the Environment

Open the `.env` file in the project folder (copy from `.env.example` if it does not exist) and fill in your details:

```
USE_SQLITE=false

DB_SERVER=localhost
DB_PORT=
DB_NAME=adbn_instant_card
DB_USER=sa
DB_PASSWORD=YourSQLServerPassword

SECRET_KEY=paste-a-long-random-key-here
```

**Important notes:**

- **`DB_SERVER`** — use `localhost` for a default SQL Server instance, or `localhost\INSTANCENAME` for a named instance (e.g. `localhost\SHREYA`). Check the exact name in SSMS at the top of Object Explorer.
- **`DB_PORT`** — leave blank if using a named instance (it uses a dynamic port). Only set this to `1433` for a default instance.
- **`DB_PASSWORD`** — must not be empty. Use your actual SA password.
- **`SECRET_KEY`** — generate a strong key with:
  ```bat
  python -c "import secrets; print(secrets.token_hex(32))"
  ```

---

### Step 6 — Run the Installer

Double-click **`install.bat`**. It will:

1. Check Python is installed (tries `python` and `py`)
2. Check ODBC Driver 17 is installed
3. Create a Python virtual environment (`venv\`)
4. Install all required packages from `requirements.txt`
5. Open `.env` in Notepad if it does not exist yet
6. Run `migrate.py` — adds all required database columns automatically
7. Run `fix_roles.py` — fixes any legacy role/status data (safe on fresh installs)
8. Import all 285 branches from `branches.json`

> **Note:** Steps 6–8 require the database and `.env` to be configured correctly. If any step shows a warning, complete the `.env` setup and re-run `install.bat`, or run the scripts manually (see Step 8).

---

### Step 7 — Start the Application

Double-click **`start.bat`**. It will run any pending migrations then start the Flask/Waitress server.

Open your browser and go to: **http://localhost:5000**

Log in with the default admin credentials:

| Field | Value |
|---|---|
| Staff ID | `ADMIN001` |
| Password | `Admin@1234` |

> **Change this password immediately** after first login via the navbar → **Change Password**.

---

### Step 8 — Import Branches (if dropdown is empty)

If the branch dropdown when adding users is empty, run the import manually:

```bat
cd "D:\ADBL INSTANT CARD\adbn-instant-card"
venv\Scripts\activate.bat
python import_branches.py
```

This is safe to run multiple times — it skips branches that already exist.

---

## Updating an Existing Installation

When you pull new code onto an already-installed Windows machine:

1. Pull / copy the latest files into the project folder
2. Run the migration script to add any new database columns:
   ```bat
   cd "D:\ADBL INSTANT CARD\adbn-instant-card"
   venv\Scripts\activate.bat
   python migrate.py
   ```
3. Run the role fix script (required when upgrading from pre-checker versions):
   ```bat
   python fix_roles.py
   ```
4. Restart `start.bat`

> Both scripts are safe to run multiple times — they skip work that is already done.

---

## Default Admin Login

| Field | Value |
|---|---|
| Staff ID | `ADMIN001` |
| Password | `Admin@1234` |

> **Change this password immediately after first login.**
> Go to the navbar → **Change Password**.

---

## Daily Use (After Installation)

- Double-click **`start.bat`** to start the server each time.
- Open browser: **http://localhost:5000**
- Press `CTRL+C` in the command window to stop the server.

---

## Adding Branch Users

1. Log in as Admin
2. Go to **Users → Add New User**
3. Fill in Staff ID, Full Name, Branch (searchable dropdown), Role (`maker` or `checker`), and Password
4. Phone and Username are optional
5. Branch staff can then log in according to their role

---

## Project Structure

```
adbn_instant_card\
├── app.py                  # Flask application entry point
├── config.py               # Database configuration (SQL Server / SQLite toggle)
├── models.py               # Database models (User, Branch, CardRequest, CardSale)
├── migrate.py              # Database migration script — run after updates
├── fix_roles.py            # One-time data fix for legacy role/status values
├── requirements.txt        # Python dependencies
├── branches.json           # All 285 ADBN branches (used by import_branches.py)
├── import_branches.py      # One-time branch seeding script
├── serve.py                # Production WSGI entry point (Waitress)
├── .env                    # Your local configuration (do not share)
├── .env.example            # Template for .env
├── install.bat             # Windows one-click installer
├── start.bat               # Windows launcher (runs migrations + starts server)
├── routes\
│   ├── auth.py             # Login / Logout / Change Password
│   ├── branch.py           # Maker dashboard, card request, mark received, card sales
│   ├── checker.py          # Checker dashboard, approve/reject requests
│   └── admin.py            # Admin panel, approvals, dispatch, exports, user management
├── utils\
│   └── exports.py          # PDF and Excel export logic
└── templates\
    ├── base.html           # Main layout with sidebar, navbar and bell notification
    ├── auth\
    │   ├── login.html
    │   └── change_password.html
    ├── branch\
    │   ├── dashboard.html
    │   ├── new_request.html
    │   └── view_request.html
    ├── checker\
    │   ├── dashboard.html
    │   └── review_request.html
    └── admin\
        ├── dashboard.html
        ├── requests.html
        ├── review_request.html
        ├── users.html
        └── new_user.html
```

---

## Card Request Fields

| Field | Description |
|---|---|
| Quantity | Number of blank instant cards required (minimum 1) |
| Card Type | Visa Card / Domestic Card / UnionPay Card |
| Mobile Number | Staff contact number for this request |
| Remarks | Optional notes for Head Office |
| Branch Info | Auto-filled from logged-in user's profile |
| Staff ID | Auto-filled from session |

---

## Troubleshooting

**`python` is not recognized when running install.bat:**
- Python is not in PATH. Re-run the Python installer → choose **Modify** → check **"Add Python to environment variables"**
- Or verify with: `python --version` and `py --version` in Command Prompt

**App crashes after pulling new code (`no such column` error):**
- Run the migration script:
  ```bat
  venv\Scripts\activate.bat
  python migrate.py
  ```
  Then restart `start.bat`.

**Admin dashboard shows no requests after upgrade:**
- Run `fix_roles.py` to tag legacy requests:
  ```bat
  venv\Scripts\activate.bat
  python fix_roles.py
  ```

**`pyodbc` fails to install (build error / wheel error):**
- Install **Microsoft C++ Build Tools** from https://visualstudio.microsoft.com/visual-cpp-build-tools/ — select "Desktop development with C++"
- Or check if pyodbc is already installed: `pip show pyodbc`

**`sqlcmd` or app cannot connect to SQL Server (TCP error):**
- TCP/IP is likely disabled. Follow Step 2 above to enable it in SQL Server Configuration Manager and restart the SQL Server service
- Verify with: `sqlcmd -S localhost -U sa -Q "SELECT @@VERSION"`

**Named instance connection fails (e.g. `localhost\SHREYA`):**
- Make sure **SQL Server Browser** service is Running (`services.msc`)
- Leave `DB_PORT` blank in `.env` — named instances use dynamic ports, not 1433
- Verify the exact instance name from SSMS Object Explorer and use that in `DB_SERVER`

**App connects via SSMS but not via the app:**
- SSMS uses Shared Memory (local only); the app uses TCP/IP — make sure TCP/IP is enabled (Step 2)

**Branch dropdown is empty when adding users:**
- Run branch import manually:
  ```bat
  cd "D:\ADBL INSTANT CARD\adbn-instant-card"
  venv\Scripts\activate.bat
  python import_branches.py
  ```

**Tables not created / app crashes on first run:**
- Make sure `adbn_instant_card` database exists in SQL Server before running `start.bat`
- Make sure `.env` has the correct credentials and `USE_SQLITE=false`

**Port 5000 already in use:**
- Change `APP_PORT=5001` in `.env`
- Then access via http://localhost:5001

**Forgot admin password:**
- Reset via another admin account: **User Management → Reset Password**
- Or open SSMS and run:
  ```sql
  -- First generate a new hash with:
  -- python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('NewPassword'))"
  UPDATE [users] SET password_hash = '<generated_hash>' WHERE staff_id = 'ADMIN001';
  ```

**Using Windows Authentication instead of SQL login:**
- Leave `DB_USER` and `DB_PASSWORD` blank in `.env`
- Update `config.py` manually:
  ```python
  _conn_str = (
      "DRIVER={ODBC Driver 17 for SQL Server};"
      f"SERVER={_server};DATABASE={DB_NAME};Trusted_Connection=yes"
  )
  ```

---

## Mac / Linux (Development / Testing)

No SQL Server or ODBC driver needed. The app uses a local SQLite file instead.

```bash
python3 -m venv venv
source venv/bin/activate
pip install flask flask-login flask-sqlalchemy flask-wtf wtforms sqlalchemy werkzeug python-dotenv reportlab openpyxl
```

Create a `.env` file with:
```
USE_SQLITE=true
SECRET_KEY=any-random-string-for-local-dev
```

Then run:
```bash
python3 import_branches.py
python3 app.py
```

Open your browser at **http://localhost:5000** and log in with `ADMIN001` / `Admin@1234`.

---

