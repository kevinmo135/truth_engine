from fetcher.congress_api import fetch_recent_federal_bills
from fetcher.florida_scraper import fetch_recent_florida_bills
from analyzer.summary import summarize_bill
from analyzer.cache_manager import get_cache
from writer.report_generator import create_digest, parse_gpt4_analysis
from notifier.email import send_email_report

import os
import argparse
import threading
import schedule
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def show_cache_stats():
    """Display cache statistics"""
    cache = get_cache()
    stats = cache.get_cache_stats()

    print("📊 Cache Statistics:")
    print(f"   📄 Total cached bills: {stats['total_cached_bills']}")
    print(f"   🔄 Total cache hits: {stats['total_cache_hits']}")
    print(f"   💰 OpenAI calls saved: {stats['estimated_openai_calls_saved']}")

    if stats['total_cached_bills'] > 0:
        print(
            f"   💲 Estimated cost savings: ~${stats['estimated_openai_calls_saved'] * 0.03:.2f}")

    return stats


def generate_and_send_digest():
    print("📥 Fetching ALL federal and Florida bills...")
    # Gets ALL available federal bills (no limit)
    federal = fetch_recent_federal_bills()
    florida = fetch_recent_florida_bills()  # Gets ALL active Florida bills
    all_bills = federal + florida

    # Show cache stats before processing
    cache_stats = show_cache_stats()

    print(f"🧠 Summarizing {len(all_bills)} bills...")
    reports = []
    for i, bill in enumerate(all_bills):
        bill_id = bill.get('bill_id', f"bill_{i+1}")
        print(
            f"🔍 Analyzing bill {i+1}/{len(all_bills)}: {bill_id} - {bill['title'][:50]}...")

        # Get bill status for proper caching
        bill_status = bill.get('status', 'Active').lower()

        analysis_content = summarize_bill(
            bill["title"], bill["summary"], bill["sponsor"], bill_id, bill_status)
        parsed_analysis = parse_gpt4_analysis(analysis_content)

        report = {
            "title": bill['title'],
            "sponsor": bill['sponsor'],
            "original_summary": bill['summary'],
            "analysis": analysis_content,
            "parsed": parsed_analysis,
            # Use original bill_id, fallback to bill_N
            "bill_id": bill.get('bill_id', f"bill_{i+1}"),
            # Use proper bill number
            "bill_number": bill.get('bill_number', bill.get('bill_id', f"bill_{i+1}")),
            "source_url": bill.get('source_url'),  # Include source URL
            "source": bill.get('source', 'unknown'),  # Include source type
            "state": bill.get('state', 'Unknown'),  # Include state
            "chamber": bill.get('chamber', 'Unknown'),  # Include chamber
            "session": bill.get('session', 'Unknown'),  # Include session
            "status": bill.get('status', 'Unknown'),  # Include status
        }
        reports.append(report)

    print("📝 Creating digest...")
    create_digest(reports)

    # Show final cache statistics
    print("\n📊 Final Cache Statistics:")
    final_stats = show_cache_stats()

    if os.getenv("EMAIL_USERNAME") and os.getenv("EMAIL_PASSWORD"):
        print("📤 Sending email...")
        send_email_report(
            subject="Daily Truth Digest",
            content=open("data/latest_digest.md").read(),
            to_address=os.getenv("EMAIL_TO", os.getenv("EMAIL_USERNAME"))
        )


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


def run_scheduler():
    """
    Background scheduler that runs daily data refresh
    """
    # Schedule daily refresh at 6:00 AM EST
    schedule.every().day.at("06:00").do(daily_refresh_job)

    print("📅 Truth Engine scheduler started")
    print("⏰ Daily refresh scheduled for 6:00 AM EST")

    # Run initial refresh when scheduler starts
    print("🔄 Running initial data refresh...")
    daily_refresh_job()

    # Keep the scheduler running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


def start_web_server(with_scheduler=True):
    import uvicorn
    print("🌐 Starting FastAPI server...")

    # Debug: Check environment variables
    print(
        f"🔧 Debug - OPENAI_API_KEY present: {bool(os.getenv('OPENAI_API_KEY'))}")
    print(
        f"🔧 Debug - CONGRESS_API_KEY present: {bool(os.getenv('CONGRESS_API_KEY'))}")
    print(f"🔧 Debug - PORT: {os.getenv('PORT', '8000')}")

    if with_scheduler:
        try:
            # Start scheduler in background thread
            print("🕐 Starting daily refresh scheduler in background...")
            scheduler_thread = threading.Thread(
                target=run_scheduler, daemon=True)
            scheduler_thread.start()
            print("✅ Scheduler started successfully")
        except Exception as e:
            print(f"⚠️ Warning: Could not start scheduler: {e}")
            print("🌐 Continuing with web server only...")

    # Start web server
    print("🚀 Starting web server on port 8000...")
    try:
        uvicorn.run("webapp.main:app", host="0.0.0.0", port=8000, reload=False)
    except Exception as e:
        print(f"❌ Failed to start web server: {e}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true",
                        help="Generate and email today's digest")
    parser.add_argument("--web", action="store_true", help="Start web server")
    parser.add_argument("--scheduler", action="store_true",
                        help="Start scheduler only")
    parser.add_argument("--no-scheduler", action="store_true",
                        help="Start web server without scheduler")
    parser.add_argument("--cache-stats", action="store_true",
                        help="Show cache statistics")
    parser.add_argument("--clear-cache", action="store_true",
                        help="Clear analysis cache")
    parser.add_argument("--cleanup", action="store_true",
                        help="Clean up old bills (older than 1 month)")
    args = parser.parse_args()

    if args.cache_stats:
        show_cache_stats()
    elif args.clear_cache:
        cache = get_cache()
        cache.clear_cache()
        print("🗑️ Cache cleared successfully")
    elif args.cleanup:
        cache = get_cache()
        cleaned_count = cache.cleanup_old_bills()
        print(f"🗑️ Cleaned up {cleaned_count} old bills")
    elif args.run:
        generate_and_send_digest()
    elif args.scheduler:
        run_scheduler()
    elif args.web:
        start_web_server(with_scheduler=not args.no_scheduler)
    else:
        # Default: start web server with scheduler
        start_web_server(with_scheduler=True)
