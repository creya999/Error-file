from flask import Flask
from flask_login import LoginManager, current_user
from config import Config
from models import db, User, CardRequest

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.context_processor
    def inject_notifications():
        """Inject received_count so admin sidebar can show a notification badge."""
        if current_user.is_authenticated and current_user.role == 'admin':
            received_count = CardRequest.query.filter_by(status='Received', admin_acknowledged=False).count()
        else:
            received_count = 0
        return dict(received_count=received_count)

    # Register blueprints
    from routes.auth    import auth_bp
    from routes.branch  import branch_bp
    from routes.admin   import admin_bp
    from routes.checker import checker_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(branch_bp, url_prefix='/branch')
    app.register_blueprint(admin_bp,  url_prefix='/admin')
    app.register_blueprint(checker_bp, url_prefix='/checker')

    # Create tables on first run
    with app.app_context():
        db.create_all()
        _seed_admin(app)

    return app


def _seed_admin(app):
    """Create default admin account if none exists."""
    with app.app_context():
        if not User.query.filter_by(role='admin').first():
            admin = User(
                staff_id    = 'ADMIN001',
                full_name   = 'System Administrator',
                phone       = '9800000000',
                branch_code = 'HO',
                branch_name = 'Head Office',
                role        = 'admin',
            )
            admin.set_password('Admin@1234')
            db.session.add(admin)
            db.session.commit()
            print('[INFO] Default admin created  →  staff_id: ADMIN001 | password: Admin@1234')


if __name__ == '__main__':
    app = create_app()
    # Development only — use serve.py (waitress) for production
    app.run(debug=False, host='0.0.0.0', port=5000)
