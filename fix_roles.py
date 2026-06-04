"""
fix_roles.py — one-time migration
-----------------------------------
Fixes two data problems introduced by the old admin.py bugs:

  1. Users created with role='branch' (old default) → updated to role='maker'
  2. CardRequests with checker_status=NULL (pre-checker records) → updated to 'Legacy'
     so the admin dashboard filter no longer leaks unreviewed requests.

Run once from your project root:
    python fix_roles.py

Safe to run multiple times — already-correct rows are not touched.
"""

import sys
import os

# ── make sure we can import your app ─────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User, CardRequest

app = create_app()

with app.app_context():

    # ── Fix 1: role = 'branch' → 'maker' ─────────────────────────────────────
    bad_role_users = User.query.filter_by(role='branch').all()

    if bad_role_users:
        print(f"\n[Fix 1] Found {len(bad_role_users)} user(s) with role='branch' — updating to 'maker':")
        for u in bad_role_users:
            print(f"        staff_id={u.staff_id!r}  full_name={u.full_name!r}")
            u.role = 'maker'
        db.session.commit()
        print(f"        ✓ Done — {len(bad_role_users)} user(s) updated.")
    else:
        print("\n[Fix 1] No users with role='branch' found — nothing to do.")

    # ── Fix 2: checker_status = NULL → 'Legacy' ───────────────────────────────
    legacy_requests = CardRequest.query.filter(
        CardRequest.checker_status == None
    ).all()

    if legacy_requests:
        print(f"\n[Fix 2] Found {len(legacy_requests)} request(s) with checker_status=NULL — updating to 'Legacy':")
        for r in legacy_requests:
            print(f"        request_no={r.request_no!r}  status={r.status!r}")
            r.checker_status = 'Legacy'
        db.session.commit()
        print(f"        ✓ Done — {len(legacy_requests)} request(s) updated.")
    else:
        print("\n[Fix 2] No requests with NULL checker_status found — nothing to do.")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n[Summary]")
    for role in ('admin', 'maker', 'checker'):
        count = User.query.filter_by(role=role).count()
        print(f"  {role:10s}: {count} user(s)")

    print("\n✓ Migration complete.\n")
