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
