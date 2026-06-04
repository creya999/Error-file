from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime
from models import db, CardRequest, Branch, CardSale

branch_bp = Blueprint('branch', __name__)

def branch_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.role not in ('maker', 'checker', 'admin'):
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

# ─── Branch Dashboard ─────────────────────────────────────────────────────────
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

# ─── New Request ──────────────────────────────────────────────────────────────
@branch_bp.route('/request/new', methods=['GET', 'POST'])
@login_required
@branch_required
def new_request():

    if current_user.role not in ('maker', 'admin'):
        flash('Only makers can submit requests.', 'danger')
        return redirect(url_for('branch.dashboard'))







    if request.method == 'POST':
        quantity = request.form.get('quantity', '').strip()
        mobile   = request.form.get('mobile', '').strip()
        remarks  = request.form.get('remarks', '').strip()
        card_type = request.form.get('card_type', '').strip()

        errors = []
        if not quantity.isdigit() or int(quantity) < 1:
            errors.append('Quantity must be a positive number.')
        if not mobile or len(mobile) < 10:
            errors.append('Valid mobile number is required.')
        if card_type not in ('Visa Card', 'NepalPay Card', 'UnionPay Card'):  # ← ADD HERE
            errors.append('Please select a valid card type.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('branch/new_request.html', form_data=request.form)

        card_request = CardRequest(
            request_no   = _generate_request_no(),
            branch_code  = current_user.branch_code,
            branch_name  = current_user.branch_name,
            staff_id     = current_user.staff_id,
            staff_phone  = mobile,
            quantity     = int(quantity),
            remarks      = remarks,
            card_type    = card_type,
            requested_by = current_user.id,
        )
        db.session.add(card_request)
        db.session.commit()
        flash(f'Card request {card_request.request_no} submitted successfully!', 'success')
        return redirect(url_for('branch.dashboard'))

    return render_template('branch/new_request.html', form_data={})

# ─── Mark Received ────────────────────────────────────────────────────────────
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

# ─── Update Cards Sold ────────────────────────────────────────────────────────
# ─── Update Cards Sold ────────────────────────────────────────────────────────
@branch_bp.route('/request/<int:req_id>/sold', methods=['GET', 'POST'])
@login_required
@branch_required
def update_sold(req_id):
    """Branch enters additional cards sold; cumulative total is tracked."""
    from datetime import date

    req = CardRequest.query.get_or_404(req_id)

    if current_user.role != 'admin' and req.branch_code != current_user.branch_code:
        flash('Access denied.', 'danger')
        return redirect(url_for('branch.dashboard'))

    if req.status != 'Received':
        flash('You can only enter sold quantity after cards are received.', 'warning')
        return redirect(url_for('branch.view_request', req_id=req_id))

    if request.method == 'POST':                                          # ← REPLACE FROM HERE
        try:
            new_sold = int(request.form.get('cards_sold', 0))
        except ValueError:
            flash('Please enter a valid number.', 'danger')
            return redirect(url_for('branch.update_sold', req_id=req_id))

        if new_sold < 1:
            flash('Please enter at least 1.', 'danger')
            return redirect(url_for('branch.update_sold', req_id=req_id))

        # Validate sold_date
        sold_date_str = request.form.get('sold_date', '')
        try:
            sold_date = datetime.strptime(sold_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Please select a valid sale date.', 'danger')
            return redirect(url_for('branch.update_sold', req_id=req_id))

        current_remaining = req.cards_remaining if req.cards_remaining is not None else req.approved_quantity

        if new_sold > current_remaining:
            flash(f'Cannot sell {new_sold}. Only {current_remaining} cards remaining.', 'danger')
            return redirect(url_for('branch.update_sold', req_id=req_id))

        # Save individual sale entry
        sale = CardSale(
            request_id  = req.id,
            cards_sold  = new_sold,
            sold_date   = sold_date,
            recorded_by = current_user.full_name,
        )
        db.session.add(sale)

        # Update cumulative totals on the request
        previous_sold       = req.cards_sold or 0
        req.cards_sold      = previous_sold + new_sold
        req.cards_remaining = current_remaining - new_sold
        db.session.commit()

        flash(f'Updated! {new_sold} sold on {sold_date}. Total sold: {req.cards_sold} | Remaining: {req.cards_remaining}', 'success')
        return redirect(url_for('branch.view_request', req_id=req_id))   # ← REPLACE TO HERE

    return render_template('branch/update_sold.html', req=req,
                           today=date.today().isoformat())
# ─── View Request ─────────────────────────────────────────────────────────────
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

    # ─── Sold Summary ─────────────────────────────────────────────────────────────
@branch_bp.route('/sold-summary')
@login_required
@branch_required
def sold_summary():
    """Lists all Received requests so branch can update sold quantity."""
    requests = (CardRequest.query
                .filter_by(branch_code=current_user.branch_code, status='Received')
                .order_by(CardRequest.requested_at.desc())
                .all())
    return render_template('branch/sold_summary.html', requests=requests)
