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

    id            = db.Column(db.Integer, primary_key=True)
    staff_id      = db.Column(db.String(50), unique=True, nullable=False)
    username      = db.Column(db.String(50), unique=True, nullable=True)   # optional login alias
    full_name     = db.Column(db.String(150), nullable=False)
    phone         = db.Column(db.String(20), nullable=False)
    branch_code   = db.Column(db.String(20), nullable=False)
    branch_name   = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='maker')  # 'maker' | 'checker' | 'admin'
    is_active     = db.Column(db.Boolean, default=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

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

    id                = db.Column(db.Integer, primary_key=True)
    request_no        = db.Column(db.String(30), unique=True, nullable=False)   # e.g. ADBN-2024-00001
    branch_code       = db.Column(db.String(20), nullable=False)
    branch_name       = db.Column(db.String(150), nullable=False)
    staff_id          = db.Column(db.String(50), nullable=False)
    staff_phone       = db.Column(db.String(20), nullable=False)
    quantity          = db.Column(db.Integer, nullable=False)
    approved_quantity = db.Column(db.Integer, nullable=True)   # Set by admin on approval
    remarks           = db.Column(db.String(500))
    status            = db.Column(db.String(20), default='Pending')  # Pending|Approved|Rejected|Dispatched|Received
    admin_remarks     = db.Column(db.String(500))
    requested_by      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    requested_at      = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_by       = db.Column(db.String(100))
    reviewed_at       = db.Column(db.DateTime)
    dispatched_by     = db.Column(db.String(100))
    dispatched_at     = db.Column(db.DateTime)
    dispatch_remarks  = db.Column(db.String(500))
    received_at       = db.Column(db.DateTime)
    received_by       = db.Column(db.String(100))
    admin_acknowledged = db.Column(db.Boolean, default=False)  # True once admin has seen received status

    
    # ── Checker workflow ──────────────────────────────────────────────────────────
    checker_status   = db.Column(db.String(20), default='Pending')   # Pending|Approved|Rejected
    checker_remarks  = db.Column(db.String(500))
    checked_by       = db.Column(db.String(100))
    checked_at       = db.Column(db.DateTime)
    
    
    
    
    # ── NEW: Card sales tracking (entered by branch after receiving) ──────────
    cards_sold      = db.Column(db.Integer, nullable=True)   # how many cards branch has sold
    cards_remaining = db.Column(db.Integer, nullable=True)   # approved_quantity - cards_sold
    card_type       = db.Column(db.String(50), nullable=True)   # Visa Card | Domestic Card | UnionPay Card  
    sold_date       = db.Column(db.Date, nullable=True)          # date of last sold update                  

    def __repr__(self):
        return f'<CardRequest {self.request_no} | {self.status}>'
# ─────────────────────────────────────────
# Individual Card Sale entries
# ─────────────────────────────────────────
class CardSale(db.Model):
    __tablename__ = 'card_sales'

    id           = db.Column(db.Integer, primary_key=True)
    request_id   = db.Column(db.Integer, db.ForeignKey('card_requests.id'), nullable=False)
    cards_sold   = db.Column(db.Integer, nullable=False)
    sold_date    = db.Column(db.Date, nullable=False)
    recorded_by  = db.Column(db.String(100))
    recorded_at  = db.Column(db.DateTime, default=datetime.utcnow)

    request = db.relationship('CardRequest', backref='sales', lazy=True)

    def __repr__(self):
        return f'<CardSale req={self.request_id} sold={self.cards_sold} date={self.sold_date}>'