from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from config.extensions import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    fname = db.Column(db.String(25))
    lname = db.Column(db.String(25))
    email = db.Column(db.String(120), unique=True, nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    phone = db.Column(db.String(10))
    reg_no = db.Column(db.String(15))
    address = db.Column(db.String(20))
    active = db.Column(db.Boolean,default=True)
    profile_image = db.Column(db.String(200), default='images/person.png')
    role = db.Column(db.String(10), nullable=False, default='user')

class EmailOTP(db.Model):
    __tablename__ = "email_otp"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    otp = db.Column(db.String(7), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
