from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "send_daily_reminder": {
        "task": "backend.celery.tasks.send_daily_reminder",
        "schedule": crontab(hour=10, minute=00)
    },

    "send_monthly_activity_report": {
        "task": "backend.celery.tasks.send_monthly_activity_report",
        "schedule": crontab(hour=23,minute=30)
    },
    
    'check-overtime-bookings-every-30-mins': {
        'task': 'backend.celery.tasks.check_overtime_bookings',
        'schedule': 30 * 60,
    }
}