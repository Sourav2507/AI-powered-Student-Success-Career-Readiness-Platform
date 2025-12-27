from flask import Blueprint, request, jsonify,render_template
from datetime import datetime, timedelta
from backend.app.model.models import User,EmailOTP,PhoneOTP
from backend.app.async_celery.tasks import demo_async_task
from backend.app.utils.otp import generate_otp
from backend.app.async_celery.tasks import send_otp_email, send_sms_otp
from backend.app.config.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash


auth = Blueprint('auth', __name__, template_folder='templates', url_prefix='/auth')

@auth.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template("login.html")
    
    elif request.method == 'POST':
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
    
    else:
        return jsonify(success=False, error="Invalid request method"), 405


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template("register.html")

    data = request.get_json()
    if not data:
        return jsonify(success=False, error="No JSON data provided"), 400

    # REQUIRED
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify(
            success=False,
            error="Username, email and password are required"
        ), 400

    # DUPLICATE CHECK
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

    # OPTIONAL FIELDS (safe extraction)
    fname = data.get('first_name') or None
    lname = data.get('last_name') or None
    age = data.get('age') or None
    gender = data.get('gender') or None
    reg_no = data.get('reg_number') or None
    address = data.get('address') or None
    phone = data.get('phone') or None  # future-proof

    # CREATE USER
    user = User(
        username=username,
        email=email,
        password=hashed_password,
        fname=fname,
        lname=lname,
        age=int(age) if age else None,
        gender=gender,
        reg_no=reg_no,
        address=address,
        phone=phone
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

@auth.route('/delete_users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)

    if not user:
        return jsonify(
            success=False,
            error="User not found"
        ), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify(
        success=True,
        message=f"User with id {user_id} deleted successfully"
    ), 200




@auth.route("/login-check", methods=["POST"])
def login_check():
    email = request.json.get("email", "").lower().strip()
    user = User.query.filter_by(email=email).first()
    return jsonify({"exists": bool(user)})


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
def verify_email_otp():
    data = request.get_json() or {}

    email = data.get("email", "").strip().lower()
    otp = data.get("otp", "").strip().upper()

    if not email or not otp:
        return jsonify(success=False, error="Email and OTP required"), 400

    # ✅ Always fetch latest unverified OTP
    record = (
        EmailOTP.query
        .filter_by(email=email, verified=False)
        .order_by(EmailOTP.expires_at.desc())
        .first()
    )

    if not record:
        return jsonify(success=False, error="No OTP found. Please resend OTP."), 400

    # Expiry check
    if datetime.utcnow() > record.expires_at:
        return jsonify(success=False, error="OTP expired. Please resend."), 400

    # Mismatch check
    if record.otp != otp:
        return jsonify(success=False, error="Invalid OTP"), 400

    # Mark verified
    record.verified = True
    db.session.commit()

    return jsonify(success=True, message="Email verified successfully")


@auth.route("/send-phone-otp", methods=["POST"])
def send_phone_otp():
    phone = request.json.get("phone", "").strip()
    if not phone:
        return jsonify(success=False, error="Phone number required"), 400

    PhoneOTP.query.filter_by(phone=phone, verified=False).delete()

    otp = generate_otp()
    expires_at = datetime.utcnow() + timedelta(seconds=290)

    record = PhoneOTP(phone=phone, otp=otp, expires_at=expires_at)
    db.session.add(record)
    db.session.commit()

    send_sms_otp.delay(phone, otp)

    return jsonify(success=True, message="OTP sent")


@auth.route("/verify-phone-otp", methods=["POST"])
def verify_phone_otp():
    data = request.get_json() or {}

    phone = data.get("phone", "").strip()
    otp = data.get("otp", "").strip().upper()

    if not phone or not otp:
        return jsonify(success=False, error="Phone and OTP required"), 400

    # 🔐 Always validate the LATEST unverified OTP
    record = (
        PhoneOTP.query
        .filter_by(phone=phone, verified=False)
        .order_by(PhoneOTP.expires_at.desc())
        .first()
    )

    if not record:
        return jsonify(success=False, error="No OTP found. Please request again."), 400

    # ⏱️ Expiry check
    if datetime.utcnow() > record.expires_at:
        return jsonify(success=False, error="OTP expired. Please request a new one."), 400

    # ❌ OTP mismatch
    if record.otp != otp:
        return jsonify(success=False, error="Invalid OTP"), 400

    # ✅ Mark verified
    record.verified = True
    db.session.commit()

    return jsonify(success=True, message="Phone verified successfully")
