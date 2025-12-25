from celery import shared_task
from flask_mail import Message
from config.extensions import mail
from flask import current_app,render_template_string
from datetime import datetime,timedelta
from weasyprint import HTML
from sqlalchemy import func
from zoneinfo import ZoneInfo
import time,re,os,uuid
from model.models import *


@shared_task(bind=True)
def demo_async_task(self):
    time.sleep(1)
    return f"Hello User, async task completed!"

@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3, "countdown": 5})
def send_otp_email(self, email, otp):
    msg = Message(
        subject="Your OTP Verification Code",
        sender=current_app.config["MAIL_USERNAME"],
        recipients=[email],
        body=(
            "Hello,\n\n"
            f"Your OTP is: {otp}\n"
            "Valid for 290 seconds.\n\n"
            "Regards,\nParksy Team"
        )
    )
    mail.send(msg)
    print(f"OTP email sent to {email} with OTP: {otp}")