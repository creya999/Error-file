import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'adbn-instant-card-secret-2024')

    # ── Session Security ───────────────────────────────────────────────────────
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=60)   # Auto-logout after 60 min idle
    SESSION_COOKIE_HTTPONLY    = True                     # JS cannot read session cookie
    SESSION_COOKIE_SAMESITE    = 'Lax'                   # Reduce CSRF exposure

    # ── Database ──────────────────────────────────────────────────────────────
    # Set USE_SQLITE=true in .env (or environment) to use SQLite for local/Mac testing.
    # Leave unset (or false) to use SQL Server (Windows production).
    USE_SQLITE = os.environ.get('USE_SQLITE', 'false').lower() == 'true'

    if USE_SQLITE:
        # SQLite — no server needed, stores data in a local file
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'adbn_test.db')}"
    else:
        # SQL Server — production (Windows)
        DB_SERVER   = os.environ.get('DB_SERVER', 'localhost')
        DB_PORT     = os.environ.get('DB_PORT', '')
        DB_NAME     = os.environ.get('DB_NAME', 'adbn_instant_card')
        DB_USER     = os.environ.get('DB_USER', 'sa')
        DB_PASSWORD = os.environ.get('DB_PASSWORD', 'your_password')

        if DB_PORT:
            _server = f"{DB_SERVER},{DB_PORT}"
        else:
            _server = DB_SERVER

        _conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={_server};"
            f"DATABASE={DB_NAME};"
            f"UID={DB_USER};"
            f"PWD={DB_PASSWORD}"
        )
        SQLALCHEMY_DATABASE_URI = f"mssql+pyodbc:///?odbc_connect={_conn_str}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
