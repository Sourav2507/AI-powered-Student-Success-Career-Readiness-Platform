from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from model.models import User,EmailOTP
from async_celery.tasks import demo_async_task
from utils.otp import generate_otp
from async_celery.tasks import send_otp_email
from config.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash


auth = Blueprint('auth', __name__, template_folder='templates', url_prefix='/auth')

@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data:
        return jsonify(success=False, error="No JSON data provided"), 400

    username_or_email = data.get('username')
    password = data.get('password')

    if not username_or_email or not password:
        return jsonify(success=False, error="Username and password required"), 400

    user = User.query.filter(
        (User.username == username_or_email) |
        (User.email == username_or_email)
    ).first()

    if not user:
        return jsonify(success=False, error="User not found"), 404

    if not user.active:
        return jsonify(success=False, error="Account is deactivated"), 403

    if not check_password_hash(user.password, password):
        return jsonify(success=False, error="Invalid credentials"), 401

    return jsonify(
        success=True,
        message="Login successful",
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "profile_image": user.profile_image
        }
    ), 200


@auth.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data:
        return jsonify(success=False, error="No JSON data provided"), 400

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify(
            success=False,
            error="Username, email and password are required"
        ), 400

    existing_user = User.query.filter(
        (User.username == username) |
        (User.email == email)
    ).first()

    if existing_user:
        return jsonify(
            success=False,
            error="Username or email already exists"
        ), 409

    hashed_password = generate_password_hash(password)

    user = User(
        username=username,
        email=email,
        password=hashed_password
    )

    db.session.add(user)
    db.session.commit()

    return jsonify(
        success=True,
        message="User registered successfully",
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
    ), 201


@auth.route("/run-task")
def run_task():
    result = demo_async_task.delay()
    return {
        "task_id": result.id,
        "status": "Task submitted"
    }

@auth.route("/send-otp", methods=["POST"])
def send_otp():
    email = request.json.get("email", "").lower().strip()
    if not email:
        return jsonify(success=False, error="Email required"), 400

    EmailOTP.query.filter_by(email=email, verified=False).delete()

    otp = generate_otp()
    expires_at = datetime.utcnow() + timedelta(seconds=290)

    record = EmailOTP(email=email, otp=otp, expires_at=expires_at)
    db.session.add(record)
    db.session.commit()

    send_otp_email.delay(email, otp)
    return jsonify(success=True, message="OTP sent")


@auth.route("/verify-otp", methods=["POST"])
def verify_otp():
    email = request.json.get("email", "").lower().strip()
    otp = request.json.get("otp", "").upper().strip()

    record = EmailOTP.query.filter_by(
        email=email,
        otp=otp,
        verified=False
    ).first()

    if not record:
        return jsonify(success=False, error="Invalid OTP"), 400

    if datetime.utcnow() > record.expires_at:
        return jsonify(success=False, error="OTP expired"), 400

    record.verified = True
    db.session.commit()

    return jsonify(success=True, message="OTP verified")
