from apscheduler.schedulers.background import BackgroundScheduler

from database.models import cleanup_database


scheduler = BackgroundScheduler()

# Cleanup the database every day at 3:00 AM
scheduler.add_job(cleanup_database, 'cron', hour=3, minute=0)
