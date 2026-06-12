from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime
from models import db, CardRequest, Branch

branch_bp = Blueprint('branch', __name__)


def branch_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.role not in ('branch', 'admin'):
            flash('Access denied.', 'danger')
            return redirect(url_for('auth.index'))
        return f(*args, **kwargs)
    return decorated


def _generate_request_no():
    """Generate sequential request number: ADBL-YYYY-NNNNN"""
    year = datetime.utcnow().year
    last = (CardRequest.query
            .filter(CardRequest.request_no.like(f'ADBL-{year}-%'))
            .order_by(CardRequest.id.desc())
            .first())
    seq = 1
    if last:
        try:
            seq = int(last.request_no.split('-')[-1]) + 1
        except ValueError:
            pass
    return f'ADBL-{year}-{seq:05d}'


@branch_bp.route('/dashboard')
@login_required
@branch_required
def dashboard():
    requests = (CardRequest.query
                .filter_by(branch_code=current_user.branch_code)
                .order_by(CardRequest.requested_at.desc())
                .all())
    stats = {
        'total':    len(requests),
        'pending':  sum(1 for r in requests if r.status == 'Pending'),
        'approved': sum(1 for r in requests if r.status == 'Approved'),
        'rejected': sum(1 for r in requests if r.status == 'Rejected'),
    }
    return render_template('branch/dashboard.html', requests=requests, stats=stats)


@branch_bp.route('/request/new', methods=['GET', 'POST'])
@login_required
@branch_required
def new_request():
    if request.method == 'POST':
        quantity = request.form.get('quantity', '').strip()
        mobile   = request.form.get('mobile', '').strip()
        remarks  = request.form.get('remarks', '').strip()

        # Basic validation
        errors = []
        if not quantity.isdigit() or int(quantity) < 1:
            errors.append('Quantity must be a positive number.')
        if not mobile or len(mobile) < 10:
            errors.append('Valid mobile number is required.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('branch/new_request.html',
                                   form_data=request.form)

        card_request = CardRequest(
            request_no  = _generate_request_no(),
            branch_code = current_user.branch_code,
            branch_name = current_user.branch_name,
            staff_id    = current_user.staff_id,
            staff_phone = mobile,
            quantity    = int(quantity),
            remarks     = remarks,
            requested_by = current_user.id,
        )
        db.session.add(card_request)
        db.session.commit()
        flash(f'Card request {card_request.request_no} submitted successfully!', 'success')
        return redirect(url_for('branch.dashboard'))

    return render_template('branch/new_request.html', form_data={})


@branch_bp.route('/request/<int:req_id>/received', methods=['POST'])
@login_required
@branch_required
def mark_received(req_id):
    req = CardRequest.query.get_or_404(req_id)
    if current_user.role != 'admin' and req.branch_code != current_user.branch_code:
        flash('Access denied.', 'danger')
        return redirect(url_for('branch.dashboard'))
    if req.status != 'Dispatched':
        flash('Only dispatched requests can be marked as received.', 'danger')
        return redirect(url_for('branch.view_request', req_id=req_id))
    req.status      = 'Received'
    req.received_at = datetime.utcnow()
    req.received_by = current_user.full_name
    db.session.commit()
    flash(f'Request {req.request_no} marked as Received. Head Office has been notified.', 'success')
    return redirect(url_for('branch.view_request', req_id=req_id))


@branch_bp.route('/request/<int:req_id>')
@login_required
@branch_required
def view_request(req_id):
    req = CardRequest.query.get_or_404(req_id)
    # Branch can only view their own requests
    if current_user.role != 'admin' and req.branch_code != current_user.branch_code:
        flash('Access denied.', 'danger')
        return redirect(url_for('branch.dashboard'))
    return render_template('branch/view_request.html', req=req)
