from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime
from models import db, CardRequest

checker_bp = Blueprint('checker', __name__)


def checker_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.role not in ('checker', 'admin'):
            flash('Access denied.', 'danger')
            return redirect(url_for('auth.index'))
        return f(*args, **kwargs)
    return decorated


# ─── Checker Dashboard ────────────────────────────────────────────────────────
@checker_bp.route('/dashboard')
@login_required
@checker_required
def dashboard():
    requests = (CardRequest.query
                .filter_by(branch_code=current_user.branch_code)
                .order_by(CardRequest.requested_at.desc())
                .all())
    stats = {
        'total':    len(requests),
        'pending':  sum(1 for r in requests if r.checker_status == 'Pending'),
        'approved': sum(1 for r in requests if r.checker_status == 'Approved'),
        'rejected': sum(1 for r in requests if r.checker_status == 'Rejected'),
    }
    return render_template('checker/dashboard.html', requests=requests, stats=stats)


# ─── Review Request ───────────────────────────────────────────────────────────
@checker_bp.route('/request/<int:req_id>', methods=['GET', 'POST'])
@login_required
@checker_required
def review_request(req_id):
    req = CardRequest.query.get_or_404(req_id)

    # FIX #1 — branch access guard (unchanged, was already correct)
    if req.branch_code != current_user.branch_code and current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('checker.dashboard'))

    # FIX #2 — prevent checker from reviewing their own request
    if req.requested_by == current_user.id:
        flash('You cannot review a request you submitted yourself.', 'danger')
        return redirect(url_for('checker.dashboard'))

    # FIX #3 — prevent re-review of an already decided request
    if req.checker_status != 'Pending':
        flash(
            f'This request has already been {req.checker_status.lower()} by the checker '
            f'({req.checked_by or "unknown"}) and cannot be changed.',
            'warning'
        )
        return redirect(url_for('checker.dashboard'))

    if request.method == 'POST':
        action          = request.form.get('action')
        checker_remarks = request.form.get('checker_remarks', '').strip()

        if action == 'Approved':
            try:
                new_qty = int(request.form.get('quantity', req.quantity))
            except (ValueError, TypeError):
                new_qty = req.quantity

            if new_qty < 1:
                flash('Quantity must be at least 1.', 'danger')
                return render_template('checker/review_request.html', req=req)

            if new_qty > req.quantity:
                flash(
                    f'Quantity cannot exceed the original requested amount ({req.quantity}).',
                    'danger'
                )
                return render_template('checker/review_request.html', req=req)

            req.quantity        = new_qty
            req.remarks         = request.form.get('remarks', req.remarks or '').strip()
            req.checker_status  = 'Approved'
            req.checker_remarks = checker_remarks
            req.checked_by      = current_user.full_name
            req.checked_at      = datetime.utcnow()
            # status stays 'Pending' so admin sees it as awaiting final approval
            db.session.commit()
            flash(f'Request {req.request_no} approved and forwarded to Admin.', 'success')
            return redirect(url_for('checker.dashboard'))

        if action == 'Rejected':
            if not checker_remarks:
                flash('Please provide a reason for rejection.', 'danger')
                return render_template('checker/review_request.html', req=req)

            req.checker_status  = 'Rejected'
            req.checker_remarks = checker_remarks
            req.checked_by      = current_user.full_name
            req.checked_at      = datetime.utcnow()
            req.status          = 'Rejected'
            db.session.commit()
            flash(f'Request {req.request_no} has been rejected.', 'success')
            return redirect(url_for('checker.dashboard'))

        # FIX #4 — hard delete removed entirely. Checkers must reject, not delete.
        # Audit trail must be preserved. If you need a "recall" feature for the
        # maker, add a separate route with a soft-delete flag (is_deleted=True).

        flash('Invalid action.', 'danger')

    return render_template('checker/review_request.html', req=req)
