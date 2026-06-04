"""
Import branches from branches.json into the database.
Run once: python import_branches.py

branches.json must be in the same directory as this file.
"""
import json
import os
from app import create_app
from models import db, Branch

JSON_PATH = os.path.join(os.path.dirname(__file__), 'branches.json')

app = create_app()

with app.app_context():
    db.create_all()

    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    added   = 0
    skipped = 0

    for entry in data:
        code = str(entry.get('branch_code', '')).strip()
        name = str(entry.get('branch_name', '')).strip()
        if not code or not name:
            continue

        if Branch.query.filter_by(branch_code=code).first():
            skipped += 1
            continue

        db.session.add(Branch(branch_code=code, branch_name=name))
        added += 1

    db.session.commit()
    print(f'[OK] Import complete — Added: {added} | Skipped (already exists): {skipped}')
