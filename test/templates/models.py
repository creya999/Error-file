from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ─────────────────────────────────────────
# Branch master list (imported from Excel)
# ─────────────────────────────────────────
class Branch(db.Model):
    __tablename__ = 'branches'

    id          = db.Column(db.Integer, primary_key=True)
    branch_code = db.Column(db.String(20), unique=True, nullable=False)
    branch_name = db.Column(db.String(150), nullable=False)

    def __repr__(self):
        return f'<Branch {self.branch_code} | {self.branch_name}>'


# ─────────────────────────────────────────
# User / Branch staff model
# ─────────────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id           = db.Column(db.Integer, primary_key=True)
    staff_id     = db.Column(db.String(50), unique=True, nullable=False)
    username     = db.Column(db.String(50), unique=True, nullable=True)   # optional login alias
    full_name    = db.Column(db.String(150), nullable=False)
    phone        = db.Column(db.String(20), nullable=False)
    branch_code  = db.Column(db.String(20), nullable=False)
    branch_name  = db.Column(db.String(150), nullable=False)
    role         = db.Column(db.String(20), nullable=False, default='branch')  # 'branch' | 'admin'
    is_active    = db.Column(db.Boolean, default=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    requests = db.relationship('CardRequest', backref='requester', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.staff_id} | {self.branch_name}>'


# ─────────────────────────────────────────
# Card Request model
# ─────────────────────────────────────────
class CardRequest(db.Model):
    __tablename__ = 'card_requests'

    id             = db.Column(db.Integer, primary_key=True)
    request_no     = db.Column(db.String(30), unique=True, nullable=False)   # e.g. ADBN-2024-00001
    branch_code    = db.Column(db.String(20), nullable=False)
    branch_name    = db.Column(db.String(150), nullable=False)
    staff_id       = db.Column(db.String(50), nullable=False)
    staff_phone    = db.Column(db.String(20), nullable=False)
    quantity       = db.Column(db.Integer, nullable=False)
    approved_quantity = db.Column(db.Integer, nullable=True)   # Set by admin on approval; may differ from quantity
    remarks        = db.Column(db.String(500))
    status         = db.Column(db.String(20), default='Pending')  # Pending | Approved | Rejected | Dispatched | Received
    admin_remarks  = db.Column(db.String(500))
    requested_by   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    requested_at   = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_by    = db.Column(db.String(100))
    reviewed_at    = db.Column(db.DateTime)
    dispatched_by  = db.Column(db.String(100))
    dispatched_at  = db.Column(db.DateTime)
    dispatch_remarks = db.Column(db.String(500))
    received_at    = db.Column(db.DateTime)
    received_by    = db.Column(db.String(100))
    admin_acknowledged = db.Column(db.Boolean, default=False)  # True once admin has seen the received status

    def __repr__(self):
        return f'<CardRequest {self.request_no} | {self.status}>'
