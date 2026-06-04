from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime
from sqlalchemy import func
from models import db, User, CardRequest, Branch
from utils.exports import export_requests_pdf, export_requests_excel

admin_bp = Blueprint('admin', __name__)

_ADMIN_VISIBLE_STATUSES = ('Approved', 'Legacy')


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


# ─── Dashboard ────────────────────────────────────────────────────────────────
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    base_filter = CardRequest.checker_status.in_(_ADMIN_VISIBLE_STATUSES)

    # DB-side counts — no Python loops, instant even with 100k rows
    total     = db.session.query(func.count(CardRequest.id)).filter(base_filter).scalar() or 0
    pending   = db.session.query(func.count(CardRequest.id)).filter(base_filter, CardRequest.status == 'Pending').scalar() or 0
    approved  = db.session.query(func.count(CardRequest.id)).filter(base_filter, CardRequest.status == 'Approved').scalar() or 0
    rejected  = db.session.query(func.count(CardRequest.id)).filter(base_filter, CardRequest.status == 'Rejected').scalar() or 0
    total_qty = (db.session.query(func.sum(CardRequest.approved_quantity))
                 .filter(base_filter, CardRequest.status == 'Approved')
                 .scalar() or 0)

    stats = {
        'total':     total,
        'pending':   pending,
        'approved':  approved,
        'rejected':  rejected,
        'total_qty': total_qty,
    }

    # Only 10 most recent rows fetched — fast login regardless of DB size
    recent = (CardRequest.query
              .filter(base_filter)
              .order_by(CardRequest.requested_at.desc())
              .limit(10)
              .all())

    return render_template('admin/dashboard.html', stats=stats, recent=recent)


# ─── All Requests ─────────────────────────────────────────────────────────────
@admin_bp.route('/requests')
@login_required
@admin_required
def all_requests():
    status_filter = request.args.get('status', '')
    branch_filter = request.args.get('branch', '')
    date_from     = request.args.get('date_from', '')
    date_to       = request.args.get('date_to', '')

    query = CardRequest.query.filter(
        CardRequest.checker_status.in_(_ADMIN_VISIBLE_STATUSES)
    )

    if status_filter:
        query = query.filter_by(status=status_filter)
    if branch_filter:
        query = query.filter(CardRequest.branch_code == branch_filter)
    if date_from:
        try:
            query = query.filter(
                CardRequest.requested_at >= datetime.strptime(date_from, '%Y-%m-%d')
            )
        except ValueError:
            pass
    if date_to:
        try:
            query = query.filter(
                CardRequest.requested_at <= datetime.strptime(
                    date_to + ' 23:59:59', '%Y-%m-%d %H:%M:%S'
                )
            )
        except ValueError:
            pass

    requests_list = query.order_by(CardRequest.requested_at.desc()).all()
    branches      = Branch.query.order_by(Branch.branch_name).all()

    if status_filter == 'Received':
        (CardRequest.query
         .filter_by(status='Received', admin_acknowledged=False)
         .update({'admin_acknowledged': True}))
        db.session.commit()

    return render_template(
        'admin/requests.html',
        requests=requests_list,
        branches=branches,
        filters={
            'status':    status_filter,
            'branch':    branch_filter,
            'date_from': date_from,
            'date_to':   date_to,
        }
    )


# ─── Review a request ─────────────────────────────────────────────────────────
@admin_bp.route('/requests/<int:req_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def review_request(req_id):
    req = CardRequest.query.get_or_404(req_id)

    if req.status == 'Received' and not req.admin_acknowledged:
        req.admin_acknowledged = True
        db.session.commit()

    if request.method == 'POST' and req.status not in ('Pending',):
        flash(f'This request is already {req.status} and cannot be changed.', 'warning')
        return render_template('admin/review_request.html', req=req)

    if request.method == 'POST':
        action        = request.form.get('action')
        admin_remarks = request.form.get('admin_remarks', '').strip()

        if action == 'Approved':
            try:
                approved_qty = int(request.form.get('approved_quantity', req.quantity))
            except (ValueError, TypeError):
                approved_qty = req.quantity

            if approved_qty < 1:
                flash('Approved quantity must be at least 1.', 'danger')
                return render_template('admin/review_request.html', req=req)
            if approved_qty > req.quantity:
                flash(f'Approved quantity cannot exceed requested quantity ({req.quantity}).', 'danger')
                return render_template('admin/review_request.html', req=req)

            req.approved_quantity = approved_qty
            req.status            = 'Approved'
            req.admin_remarks     = admin_remarks
            req.reviewed_by       = current_user.full_name
            req.reviewed_at       = datetime.utcnow()
            db.session.commit()
            flash(f'Request {req.request_no} approved for {approved_qty} card(s).', 'success')
            return redirect(url_for('admin.all_requests'))

        if action == 'Rejected':
            if not admin_remarks:
                flash('Please provide a reason for rejection.', 'danger')
                return render_template('admin/review_request.html', req=req)

            req.status        = 'Rejected'
            req.admin_remarks = admin_remarks
            req.reviewed_by   = current_user.full_name
            req.reviewed_at   = datetime.utcnow()
            db.session.commit()
            flash(f'Request {req.request_no} has been rejected.', 'success')
            return redirect(url_for('admin.all_requests'))

        flash('Invalid action.', 'danger')

    return render_template('admin/review_request.html', req=req)


# ─── Dispatch a request ───────────────────────────────────────────────────────
@admin_bp.route('/requests/<int:req_id>/dispatch', methods=['POST'])
@login_required
@admin_required
def dispatch_request(req_id):
    req = CardRequest.query.get_or_404(req_id)
    if req.status != 'Approved':
        flash('Only approved requests can be dispatched.', 'danger')
        return redirect(url_for('admin.review_request', req_id=req_id))

    req.status           = 'Dispatched'
    req.dispatched_by    = current_user.full_name
    req.dispatched_at    = datetime.utcnow()
    req.dispatch_remarks = request.form.get('dispatch_remarks', '').strip()
    db.session.commit()
    flash(f'Request {req.request_no} marked as Dispatched.', 'success')
    return redirect(url_for('admin.review_request', req_id=req_id))


# ─── Export PDF ───────────────────────────────────────────────────────────────
@admin_bp.route('/requests/export/pdf')
@login_required
@admin_required
def export_pdf():
    status_filter = request.args.get('status', 'All')
    query = CardRequest.query
    if status_filter and status_filter != 'All':
        query = query.filter_by(status=status_filter)
    requests_list = query.order_by(CardRequest.requested_at.desc()).all()
    label    = status_filter or 'All'
    pdf_file = export_requests_pdf(requests_list, label)
    return send_file(
        pdf_file,
        as_attachment=True,
        download_name=f'ADBL_Card_Requests_{label}_{datetime.now().strftime("%Y%m%d")}.pdf',
        mimetype='application/pdf'
    )


# ─── Export Excel ─────────────────────────────────────────────────────────────
@admin_bp.route('/requests/export/excel')
@login_required
@admin_required
def export_excel():
    status_filter = request.args.get('status', 'All')
    query = CardRequest.query
    if status_filter and status_filter != 'All':
        query = query.filter_by(status=status_filter)
    requests_list = query.order_by(CardRequest.requested_at.desc()).all()
    label      = status_filter or 'All'
    excel_file = export_requests_excel(requests_list, label)
    return send_file(
        excel_file,
        as_attachment=True,
        download_name=f'ADBL_Card_Requests_{label}_{datetime.now().strftime("%Y%m%d")}.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


# ─── User Management ──────────────────────────────────────────────────────────
@admin_bp.route('/users')
@login_required
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=all_users)


@admin_bp.route('/users/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_user():
    branches = Branch.query.order_by(Branch.branch_name).all()

    if request.method == 'POST':
        staff_id         = request.form.get('staff_id', '').strip()
        username         = request.form.get('username', '').strip()
        full_name        = request.form.get('full_name', '').strip()
        phone            = request.form.get('phone', '').strip()
        branch_code      = request.form.get('branch_code', '').strip()
        branch_name      = request.form.get('branch_name', '').strip()
        role             = request.form.get('role', 'maker')
        password         = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        branch_select = request.form.get('branch_select', '').strip()
        if (not branch_code or not branch_name) and '|' in branch_select:
            parts       = branch_select.split('|', 1)
            branch_code = parts[0].strip()
            branch_name = parts[1].strip()

        errors = []
        if not staff_id:
            errors.append('Staff ID is required.')
        if not full_name:
            errors.append('Full Name is required.')
        if not branch_code or not branch_name:
            errors.append('Please select a branch from the dropdown.')
        if not password:
            errors.append('Password is required.')
        elif len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        elif password != confirm_password:
            errors.append('Password and Confirm Password do not match.')
        if User.query.filter_by(staff_id=staff_id).first():
            errors.append(f'Staff ID "{staff_id}" already exists.')
        if username and User.query.filter_by(username=username).first():
            errors.append(f'Username "{username}" is already taken.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('admin/new_user.html', form_data=request.form,
                                   branches=branches)

        user = User(
            staff_id    = staff_id,
            username    = username if username else None,
            full_name   = full_name,
            phone       = phone,
            branch_code = branch_code.upper(),
            branch_name = branch_name,
            role        = role,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash(f'User {full_name} created successfully.', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/new_user.html', form_data={}, branches=branches)


@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'danger')
        return redirect(url_for('admin.users'))
    user.is_active = not user.is_active
    db.session.commit()
    state = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.full_name} has been {state}.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_password(user_id):
    user         = User.query.get_or_404(user_id)
    new_pass     = request.form.get('new_password', '')
    confirm_pass = request.form.get('confirm_password', '')
    if len(new_pass) < 6:
        flash('Password must be at least 6 characters.', 'danger')
        return redirect(url_for('admin.users'))
    if new_pass != confirm_pass:
        flash('Passwords do not match.', 'danger')
        return redirect(url_for('admin.users'))
    user.set_password(new_pass)
    db.session.commit()
    flash(f'Password reset for {user.full_name}.', 'success')
    return redirect(url_for('admin.users'))
