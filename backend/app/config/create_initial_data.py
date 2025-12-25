from model.models import db, User
from werkzeug.security import generate_password_hash

def setup_initial_data(app):
    with app.app_context():
        db.create_all()

        admin_email = 'admin@study.iitm.ac.in'
        admin_username = 'admin'
        admin_password = 'cupcake/mad@007_admin'

        existing_admin = User.query.filter_by(email=admin_email).first()
        if existing_admin:
            return

        hashed_password = generate_password_hash(admin_password)
        admin_user = User(
            username=admin_username,
            email=admin_email,
            password=hashed_password,
            role='admin'
        )
        db.session.add(admin_user)
        db.session.commit()