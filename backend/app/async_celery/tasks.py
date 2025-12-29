from celery import shared_task
from flask_mail import Message
from backend.app.config.extensions import mail
from flask import current_app,render_template_string
from datetime import datetime,timedelta
from weasyprint import HTML
from sqlalchemy import func
from zoneinfo import ZoneInfo
import time,re,os,uuid
from backend.app.model.models import *
from twilio.rest import Client
import os
import json
import redis
import hashlib
from backend.app.utils.job_fetcher import fetch_jobs_from_adzuna

from dotenv import load_dotenv
load_dotenv()


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

@shared_task(autoretry_for=(Exception,), retry_kwargs={"max_retries": 3, "countdown": 5})
def send_sms_otp(phone, otp):
    client = Client(
        os.getenv("TWILIO_ACCOUNT_SID"),
        os.getenv("TWILIO_AUTH_TOKEN")
    )

    message = client.messages.create(
        body=f"Your Mentora verification code is: {otp}",
        from_=os.getenv("TWILIO_PHONE_NUMBER"),
        to=phone
    )

    print(f"OTP SMS sent to {phone} with OTP: {otp}")
    return message.sid



redis_client = redis.Redis(
    host="localhost",
    port=6379,
    db=2,  # 👈 use a separate DB for job cache
    decode_responses=True
)

JOB_CACHE_TTL = 60 * 15  # 15 minutes


def job_cache_key(roles, location="india"):
    raw = f"{','.join(sorted(roles))}:{location}"
    return "jobs:" + hashlib.md5(raw.encode()).hexdigest()


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 10}
)
def fetch_and_cache_jobs(self, roles, location="india"):

    cache_key = job_cache_key(roles, location)

    jobs = []
    for role in roles:
        jobs.extend(fetch_jobs_from_adzuna(role, location))

    # Deduplicate (title + company)
    seen = set()
    unique_jobs = []

    for job in jobs:
        key = (job.get("title"), job.get("company"))
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)

    redis_client.setex(cache_key, JOB_CACHE_TTL, json.dumps(unique_jobs))
    redis_client.setex(cache_key + ":status", JOB_CACHE_TTL, "ready")

    return {"count": len(unique_jobs)}
