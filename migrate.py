"""
Run database migrations — adds any missing columns to existing tables.
Safe to run multiple times; skips columns that already exist.
Run after install or after pulling updates that add new model fields.
"""

from app import create_app
from models import db
from sqlalchemy import text, inspect

# Columns to add to card_requests table
# (column_name, sqlite_type, mssql_type, default)
CARD_REQUEST_MIGRATIONS = [
    ('approved_quantity',   'INTEGER',       'INT',             None),
    ('dispatched_by',       'VARCHAR(100)',  'NVARCHAR(100)',   None),
    ('dispatched_at',       'DATETIME',      'DATETIME',        None),
    ('dispatch_remarks',    'VARCHAR(500)',  'NVARCHAR(500)',   None),
    ('received_at',         'DATETIME',      'DATETIME',        None),
    ('received_by',         'VARCHAR(100)',  'NVARCHAR(100)',   None),
    ('admin_acknowledged',  'INTEGER',       'BIT',             '0'),
    # Checker workflow
    ('checker_status',      'VARCHAR(20)',   'NVARCHAR(20)',    "'Pending'"),
    ('checker_remarks',     'VARCHAR(500)',  'NVARCHAR(500)',   None),
    ('checked_by',          'VARCHAR(100)',  'NVARCHAR(100)',   None),
    ('checked_at',          'DATETIME',      'DATETIME',        None),
    # Card sales tracking
    ('cards_sold',          'INTEGER',       'INT',             None),
    ('cards_remaining',     'INTEGER',       'INT',             None),
    ('card_type',           'VARCHAR(50)',   'NVARCHAR(50)',    None),
    ('sold_date',           'DATE',          'DATE',            None),
]

app = create_app()

with app.app_context():
    from config import Config
    is_sqlite = Config.USE_SQLITE

    with db.engine.connect() as conn:
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()

        # ── Migrate card_requests columns ─────────────────────────────────────
        existing_cols = {col['name'] for col in inspector.get_columns('card_requests')}
        added = skipped = 0

        for col_name, sqlite_type, mssql_type, default in CARD_REQUEST_MIGRATIONS:
            if col_name in existing_cols:
                skipped += 1
                continue

            sql_type = sqlite_type if is_sqlite else mssql_type

            if default is not None:
                sql = f"ALTER TABLE card_requests ADD {col_name} {sql_type} NOT NULL DEFAULT {default}"
            else:
                sql = f"ALTER TABLE card_requests ADD {col_name} {sql_type} NULL"

            try:
                conn.execute(text(sql))
                print(f'  [OK] card_requests: added column {col_name}')
                added += 1
            except Exception as e:
                print(f'  [ERROR] card_requests.{col_name}: {e}')

        # ── Create card_sales table if missing ────────────────────────────────
        if 'card_sales' not in existing_tables:
            try:
                if is_sqlite:
                    conn.execute(text("""
                        CREATE TABLE card_sales (
                            id          INTEGER PRIMARY KEY AUTOINCREMENT,
                            request_id  INTEGER NOT NULL REFERENCES card_requests(id),
                            cards_sold  INTEGER NOT NULL,
                            sold_date   DATE NOT NULL,
                            recorded_by VARCHAR(100),
                            recorded_at DATETIME
                        )
                    """))
                else:
                    conn.execute(text("""
                        CREATE TABLE card_sales (
                            id          INT IDENTITY(1,1) PRIMARY KEY,
                            request_id  INT NOT NULL REFERENCES card_requests(id),
                            cards_sold  INT NOT NULL,
                            sold_date   DATE NOT NULL,
                            recorded_by NVARCHAR(100),
                            recorded_at DATETIME
                        )
                    """))
                print('  [OK] card_sales table created.')
                added += 1
            except Exception as e:
                print(f'  [ERROR] card_sales table: {e}')
        else:
            print('  [OK] card_sales table already exists.')
            skipped += 1

        conn.commit()

    print(f'\n[OK] Migration complete — Added: {added} | Already existed: {skipped}')
