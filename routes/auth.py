from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from models import db, User

auth_bp = Blueprint('auth', __name__)


def _role_dashboard():
    """Return the correct dashboard URL for the currently logged-in user's role."""
    role_map = {
        'admin':   'admin.dashboard',
        'checker': 'checker.dashboard',
        'maker':   'branch.dashboard',
    }
    # Any unknown role falls back to the branch dashboard
    return url_for(role_map.get(current_user.role, 'branch.dashboard'))


# ─── Index / landing ──────────────────────────────────────────────────────────
@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(_role_dashboard())
    return redirect(url_for('auth.login'))


# ─── Login ────────────────────────────────────────────────────────────────────
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(_role_dashboard())

    if request.method == 'POST':
        login_input = request.form.get('staff_id', '').strip()
        password    = request.form.get('password', '')

        # Accept Staff ID or Username
        user = (User.query.filter_by(staff_id=login_input).first() or
                User.query.filter_by(username=login_input).first())

        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Contact admin.', 'danger')
                return redirect(url_for('auth.login'))

            login_user(user)
            flash(f'Welcome, {user.full_name}!', 'success')

            # FIX — validate the next param to prevent open-redirect attacks.
            # Only follow the redirect if it points to the same host (relative URL).
            next_page = request.args.get('next', '')
            if next_page:
                parsed = urlparse(next_page)
                # A safe redirect has no scheme/netloc (i.e. it is a relative path)
                if parsed.scheme or parsed.netloc:
                    next_page = ''

            return redirect(next_page or _role_dashboard())

        flash('Invalid Staff ID / Username or Password.', 'danger')

    return render_template('auth/login.html')


# ─── Logout ───────────────────────────────────────────────────────────────────
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


# ─── Change password (all roles) ─────────────────────────────────────────────
@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_pw = request.form.get('current_password', '')
        new_pw     = request.form.get('new_password', '')
        confirm_pw = request.form.get('confirm_password', '')

        if not current_user.check_password(current_pw):
            flash('Current password is incorrect.', 'danger')
        elif len(new_pw) < 6:
            flash('New password must be at least 6 characters.', 'danger')
        elif new_pw != confirm_pw:
            flash('New password and confirm password do not match.', 'danger')
        elif new_pw == current_pw:
            flash('New password must be different from the current password.', 'warning')
        else:
            current_user.set_password(new_pw)
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('auth.change_password'))

    return render_template('auth/change_password.html')
