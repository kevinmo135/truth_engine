from fetcher.federal_congress_gov import fetch_recent_federal_bills
from fetcher.florida import fetch_recent_florida_bills
from analyzer.summary import summarize_bill
from writer.report_generator import create_digest, parse_gpt4_analysis
from notifier.email import send_email_report

import os
import argparse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def generate_and_send_digest():
    print("📥 Fetching federal and Florida bills...")
    federal = fetch_recent_federal_bills()
    florida = fetch_recent_florida_bills()
    all_bills = federal + florida

    print(f"🧠 Summarizing {len(all_bills)} bills...")
    reports = []
    for i, bill in enumerate(all_bills):
        print(
            f"🔍 Analyzing bill {i+1}/{len(all_bills)}: {bill['title'][:50]}...")

        analysis_content = summarize_bill(
            bill["title"], bill["summary"], bill["sponsor"])
        parsed_analysis = parse_gpt4_analysis(analysis_content)

        report = {
            "title": bill['title'],
            "sponsor": bill['sponsor'],
            "original_summary": bill['summary'],
            "analysis": analysis_content,
            "parsed": parsed_analysis,
            "bill_id": f"bill_{i+1}",  # For web linking
            "source_url": bill.get('source_url'),  # Include source URL
            "source": bill.get('source', 'unknown'),  # Include source type
        }
        reports.append(report)

    print("📝 Creating digest...")
    create_digest(reports)

    if os.getenv("EMAIL_USERNAME") and os.getenv("EMAIL_PASSWORD"):
        print("📤 Sending email...")
        send_email_report(
            subject="Daily Truth Digest",
            content=open("data/latest_digest.md").read(),
            to_address=os.getenv("EMAIL_TO", os.getenv("EMAIL_USERNAME"))
        )


def start_web_server():
    import uvicorn
    print("🌐 Starting FastAPI server...")
    uvicorn.run("webapp.main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true",
                        help="Generate and email today's digest")
    parser.add_argument("--web", action="store_true", help="Start web server")
    args = parser.parse_args()

    if args.run:
        generate_and_send_digest()
    if args.web:
        start_web_server()
