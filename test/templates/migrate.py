"""
Run database migrations — adds any missing columns to existing tables.
Safe to run multiple times; skips columns that already exist.
Run after install or after pulling updates that add new model fields.
"""
from app import create_app
from models import db
from sqlalchemy import text, inspect

MIGRATIONS = [
    # (column_name, sql_type_sqlite, sql_type_mssql, default)
    ('approved_quantity',   'INTEGER',       'INT',             None),
    ('dispatched_by',       'VARCHAR(100)',  'NVARCHAR(100)',   None),
    ('dispatched_at',       'DATETIME',      'DATETIME',        None),
    ('dispatch_remarks',    'VARCHAR(500)',  'NVARCHAR(500)',   None),
    ('received_at',         'DATETIME',      'DATETIME',        None),
    ('received_by',         'VARCHAR(100)',  'NVARCHAR(100)',   None),
    ('admin_acknowledged',  'INTEGER',       'BIT',             '0'),
]

app = create_app()

with app.app_context():
    from config import Config
    is_sqlite = Config.USE_SQLITE

    with db.engine.connect() as conn:
        # Get existing columns
        inspector = inspect(db.engine)
        existing = {col['name'] for col in inspector.get_columns('card_requests')}

        added   = 0
        skipped = 0

        for col_name, sqlite_type, mssql_type, default in MIGRATIONS:
            if col_name in existing:
                skipped += 1
                continue

            sql_type = sqlite_type if is_sqlite else mssql_type

            if default is not None:
                sql = f"ALTER TABLE card_requests ADD {col_name} {sql_type} NOT NULL DEFAULT {default}"
            else:
                sql = f"ALTER TABLE card_requests ADD {col_name} {sql_type} NULL"

            try:
                conn.execute(text(sql))
                print(f'  [OK] Added column: {col_name}')
                added += 1
            except Exception as e:
                print(f'  [ERROR] {col_name}: {e}')

        conn.commit()

    print(f'\n[OK] Migration complete — Added: {added} | Already existed: {skipped}')
