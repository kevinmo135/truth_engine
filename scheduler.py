import schedule
import time
import os
from datetime import datetime
from main import generate_and_send_digest


def daily_refresh_job():
    """
    Job that runs daily to refresh Truth Engine data
    """
    print(f"🕐 Starting daily refresh at {datetime.now()}")
    try:
        generate_and_send_digest()
        print(f"✅ Daily refresh completed successfully at {datetime.now()}")
    except Exception as e:
        print(f"❌ Daily refresh failed: {str(e)}")


def setup_scheduler():
    """
    Set up the daily data refresh schedule
    """
    # Schedule daily refresh at 6:00 AM EST
    schedule.every().day.at("06:00").do(daily_refresh_job)

    print("📅 Truth Engine scheduler started")
    print("⏰ Daily refresh scheduled for 6:00 AM EST")
    print("🔄 Running initial data refresh...")

    # Run initial refresh
    daily_refresh_job()

    # Keep the scheduler running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


if __name__ == "__main__":
    setup_scheduler()
