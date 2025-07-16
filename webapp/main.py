from analyzer.summary import get_detailed_analysis
from analyzer.analytics import generate_analytics_report, LegislativeAnalytics
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import json
import sys
from dotenv import load_dotenv

# Add parent directory to path to import analyzer
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

app = FastAPI(title="Truth Engine",
              description="Legislative Analysis Dashboard")
app.mount("/static", StaticFiles(directory="webapp/static"), name="static")
templates = Jinja2Templates(directory="webapp/templates")


def calculate_bill_popularity(bill):
    """Calculate a popularity score for bill sorting"""
    score = 0

    # Get analytics analyzer for topic detection
    analyzer = LegislativeAnalytics()

    # Base score for all bills
    score += 10

    # Topic popularity bonus (trending topics get higher scores)
    text = f"{bill.get('title', '')} {bill.get('summary', '')}".lower()

    # High-priority topics get bonus points
    high_priority_topics = {
        'Healthcare': 25,
        'Economy': 20,
        'Immigration': 18,
        'Defense': 15,
        'Education': 12,
        'Environment': 10,
        'Technology': 8,
        'Infrastructure': 7
    }

    for topic, keywords in analyzer.topic_keywords.items():
        if any(keyword in text for keyword in keywords):
            score += high_priority_topics.get(topic, 5)
            break

    # Success prediction bonus
    try:
        prediction = analyzer.predict_success_probability(bill)
        # Higher success probability = more popular
        score += prediction['probability'] * 0.5

        # Bipartisan bills get extra points
        if 'bipartisan_bonus' in prediction['factors'] and prediction['factors']['bipartisan_bonus'] > 0:
            score += 15

    except:
        pass

    # Chamber bonus (Senate bills often more significant)
    chamber = bill.get('chamber', '').lower()
    if chamber == 'senate':
        score += 8
    elif chamber == 'house':
        score += 5

    # Federal bills get slight priority over state
    if bill.get('source', '').lower() == 'federal':
        score += 3

    # Recent bills get bonus (if we had dates)
    # For now, just add small random factor to mix things up
    import random
    score += random.uniform(0, 2)

    # Title length bonus (more descriptive titles often more important)
    title_length = len(bill.get('title', ''))
    if 50 < title_length < 150:  # Sweet spot for detailed but not overly long titles
        score += 5
    elif title_length > 150:
        score += 3

    # Summary length bonus (more detailed summaries = more complex/important bills)
    summary_length = len(bill.get('summary', ''))
    if summary_length > 500:
        score += 8
    elif summary_length > 200:
        score += 4

    return score


def sort_bills_by_popularity(bills):
    """Sort bills by popularity score (highest first)"""
    for bill in bills:
        bill['_popularity_score'] = calculate_bill_popularity(bill)

    return sorted(bills, key=lambda x: x.get('_popularity_score', 0), reverse=True)


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, limit: int = 100):
    """Main dashboard showing bills with pagination"""

    # Detect Intel Mac from user agent for server-side optimization
    user_agent = request.headers.get("user-agent", "").lower()
    is_intel_mac = ("macintosh" in user_agent or "mac os" in user_agent) and not (
        "arm" in user_agent or "apple silicon" in user_agent)

    # Reduce initial load for Intel Macs
    if is_intel_mac:
        limit = min(limit, 60)  # Cap at 60 bills for Intel Macs
    json_path = "data/latest_digest.json"

    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            data = json.load(f)
        reports = data.get('reports', [])
        generated_at = data.get('generated_at', 'Unknown')
    else:
        reports = []
        generated_at = "No data available"

    # Filter bills by status and source - SHOW ALL BILLS
    active_federal = []
    passed_federal = []
    failed_federal = []
    active_state = []
    passed_state = []
    failed_state = []

    for bill in reports:
        source = bill.get('source', '').lower()
        status = bill.get('status', '').lower()

        # Determine if federal or state
        is_federal = (source == 'federal' or 'congress' in source)

        # Categorize by status
        if status in ['passed', 'signed', 'enacted', 'signed into law', 'became law']:
            if is_federal:
                passed_federal.append(bill)
            else:
                passed_state.append(bill)
        elif status in ['failed', 'defeated', 'killed', 'died', 'vetoed', 'pocket vetoed']:
            if is_federal:
                failed_federal.append(bill)
            else:
                failed_state.append(bill)
        elif status in ['withdrawn', 'suspended']:
            if is_federal:
                # Group withdrawn with failed for simplicity
                failed_federal.append(bill)
            else:
                failed_state.append(bill)
        else:  # active, filed, referred, etc.
            if is_federal:
                active_federal.append(bill)
            else:
                active_state.append(bill)

    # Sort bill categories by popularity (most popular first)
    active_federal = sort_bills_by_popularity(active_federal)
    passed_federal = sort_bills_by_popularity(passed_federal)
    failed_federal = sort_bills_by_popularity(failed_federal)
    active_state = sort_bills_by_popularity(active_state)
    passed_state = sort_bills_by_popularity(passed_state)
    failed_state = sort_bills_by_popularity(failed_state)

    # Load ALL bills at once - no incremental loading
    initial_active_federal = active_federal  # Show all active federal bills
    initial_passed_federal = passed_federal  # Show all passed federal bills
    initial_failed_federal = failed_federal  # Show all failed federal bills
    initial_active_state = active_state      # Show all active state bills
    initial_passed_state = passed_state      # Show all passed state bills
    initial_failed_state = failed_state      # Show all failed state bills

    # Calculate comprehensive statistics from cache for Statistics tab
    comprehensive_stats = calculate_comprehensive_statistics()

    # Calculate full totals for statistics (not just loaded bills)
    full_totals = {
        "total_active_federal": len(active_federal),
        "total_passed_federal": len(passed_federal),
        "total_failed_federal": len(failed_federal),
        "total_active_state": len(active_state),
        "total_passed_state": len(passed_state),
        "total_failed_state": len(failed_state),
        "total_bills_on_page": len(active_federal) + len(passed_federal) + len(failed_federal) + len(active_state) + len(passed_state) + len(failed_state),
        "bills_loaded_so_far": len(initial_active_federal) + len(initial_passed_federal) + len(initial_failed_federal) + len(initial_active_state) + len(initial_passed_state) + len(initial_failed_state)
    }

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "reports": reports,  # Keep for backwards compatibility
        "active_federal": initial_active_federal,
        "passed_federal": initial_passed_federal,
        "failed_federal": initial_failed_federal,
        "active_state": initial_active_state,
        "passed_state": initial_passed_state,
        "failed_state": initial_failed_state,
        "generated_at": generated_at,
        # Default to active bills shown
        "total_bills": len(initial_active_federal) + len(initial_active_state),

        # All bills for load more
        "total_available_bills": len(active_federal) + len(passed_federal) + len(failed_federal) + len(active_state) + len(passed_state) + len(failed_state),
        "comprehensive_stats": comprehensive_stats,
        "full_totals": full_totals,
        "initial_load": True
    })


@app.get("/bill/{bill_id}", response_class=HTMLResponse)
async def bill_detail(request: Request, bill_id: str):
    """Detailed view of a specific bill"""
    json_path = "data/latest_digest.json"

    if not os.path.exists(json_path):
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "No data available"
        })

    with open(json_path, "r") as f:
        data = json.load(f)

    # Find the specific bill
    bill = None
    for report in data.get('reports', []):
        if report.get('bill_id') == bill_id:
            bill = report
            break

    if not bill:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Bill not found"
        })

    return templates.TemplateResponse("bill_detail.html", {
        "request": request,
        "bill": bill
    })


@app.post("/ask/{bill_id}")
async def ask_question(bill_id: str, question: str = Form(...)):
    """Interactive Q&A about a specific bill"""
    json_path = "data/latest_digest.json"

    if not os.path.exists(json_path):
        return JSONResponse({"error": "No data available"})

    with open(json_path, "r") as f:
        data = json.load(f)

    # Find the specific bill
    bill = None
    for report in data.get('reports', []):
        if report.get('bill_id') == bill_id:
            bill = report
            break

    if not bill:
        return JSONResponse({"error": "Bill not found"})

    # Generate detailed analysis based on user question
    try:
        detailed_response = get_detailed_analysis(
            bill['title'],
            bill['original_summary'],
            question,
            bill_id
        )

        return JSONResponse({
            "success": True,
            "answer": detailed_response,
            "question": question
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": f"Error generating response: {str(e)}"
        })


@app.get("/analytics", response_class=HTMLResponse)
async def analytics_dashboard(request: Request):
    """Analytics dashboard showing comprehensive trends and insights"""
    # Use comprehensive historical data from processed bills cache
    cache_path = "data/processed_bills.json"
    latest_path = "data/latest_digest.json"

    all_bills = []
    generated_at = "Unknown"

    # Load comprehensive historical data from cache
    if os.path.exists(cache_path):
        with open(cache_path, "r") as f:
            cache_data = json.load(f)

        # Convert cache format to reports format for analytics
        for bill_key, bill_data in cache_data.items():
            if isinstance(bill_data, dict) and 'analysis' in bill_data:
                # Parse the analysis to get structured data like the digest format
                from writer.report_generator import parse_gpt4_analysis
                parsed_analysis = parse_gpt4_analysis(
                    bill_data.get('analysis', ''))

                bill_report = {
                    "title": bill_data.get('title', ''),
                    "sponsor": "Unknown",  # Not available in cache
                    "original_summary": bill_data.get('summary', ''),
                    "analysis": bill_data.get('analysis', ''),
                    "parsed": parsed_analysis,
                    "bill_id": bill_data.get('bill_id', bill_key),
                    "bill_number": bill_data.get('bill_id', bill_key),
                    "source_url": None,
                    "source": "historical",
                    "state": "Unknown",
                    "chamber": "Unknown",
                    "session": "Unknown",
                    "status": bill_data.get('status', 'Unknown'),
                    "cached_date": bill_data.get('cached_date'),
                    "access_count": bill_data.get('access_count', 0)
                }
                all_bills.append(bill_report)

    # Get timestamp from latest digest if available
    if os.path.exists(latest_path):
        with open(latest_path, "r") as f:
            latest_data = json.load(f)
        generated_at = latest_data.get('generated_at', 'Unknown')

    if all_bills:
        # Generate analytics report with comprehensive data
        analytics_data = generate_analytics_report(all_bills)

        return templates.TemplateResponse("analytics.html", {
            "request": request,
            "analytics": analytics_data,
            "generated_at": generated_at
        })
    else:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "No data available for analytics"
        })


@app.get("/api/bills")
async def get_bills_api(offset: int = 0, limit: int = 100):
    """API endpoint to get more bills starting from offset"""
    json_path = "data/latest_digest.json"

    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            data = json.load(f)

        reports = data.get('reports', [])

        # Filter bills by status and source - SHOW ALL BILLS
        active_federal = []
        passed_federal = []
        failed_federal = []
        active_state = []
        passed_state = []
        failed_state = []

        for bill in reports:
            source = bill.get('source', '').lower()
            status = bill.get('status', '').lower()

            # Determine if federal or state
            is_federal = (source == 'federal' or 'congress' in source)

            # Categorize by status
            if status in ['passed', 'signed', 'enacted', 'signed into law', 'became law']:
                if is_federal:
                    passed_federal.append(bill)
                else:
                    passed_state.append(bill)
            elif status in ['failed', 'defeated', 'killed', 'died', 'vetoed', 'pocket vetoed']:
                if is_federal:
                    failed_federal.append(bill)
                else:
                    failed_state.append(bill)
            elif status in ['withdrawn', 'suspended']:
                if is_federal:
                    # Group withdrawn with failed for simplicity
                    failed_federal.append(bill)
                else:
                    failed_state.append(bill)
            else:  # active, filed, referred, etc.
                if is_federal:
                    active_federal.append(bill)
                else:
                    active_state.append(bill)

        # Sort bill categories by popularity (most popular first)
        active_federal = sort_bills_by_popularity(active_federal)
        passed_federal = sort_bills_by_popularity(passed_federal)
        failed_federal = sort_bills_by_popularity(failed_federal)
        active_state = sort_bills_by_popularity(active_state)
        passed_state = sort_bills_by_popularity(passed_state)
        failed_state = sort_bills_by_popularity(failed_state)

        # Get the next batch of bills starting from offset
        all_bills = active_federal + passed_federal + \
            failed_federal + active_state + passed_state + failed_state

        # Apply offset and limit
        paginated_bills = all_bills[offset:offset + limit]

        return {
            "bills": paginated_bills,
            "pagination": {
                "offset": offset,
                "limit": limit,
                "total_bills": len(all_bills),
                "has_more": offset + limit < len(all_bills),
                "returned_count": len(paginated_bills)
            },
            "generated_at": data.get('generated_at', 'Unknown')
        }
    else:
        return {
            "bills": [],
            "pagination": {
                "offset": offset,
                "limit": limit,
                "total_bills": 0,
                "has_more": False,
                "returned_count": 0
            },
            "generated_at": "No data available"
        }


def calculate_comprehensive_statistics():
    """Calculate comprehensive statistics from the full processed bills cache"""
    cache_path = "data/processed_bills.json"
    stats = {
        'total_bills_ever': 0,
        'total_active': 0,
        'total_passed': 0,
        'total_failed': 0,
        'total_withdrawn': 0,
        'most_accessed_bill': '',
        'cache_size_mb': 0,
        'avg_access_count': 0
    }

    if not os.path.exists(cache_path):
        return stats

    try:
        with open(cache_path, "r") as f:
            cache_data = json.load(f)

        # Calculate file size
        stats['cache_size_mb'] = round(
            os.path.getsize(cache_path) / (1024 * 1024), 1)

        total_access_count = 0
        max_access_count = 0
        most_accessed_title = ""

        for bill_key, bill_data in cache_data.items():
            if isinstance(bill_data, dict):
                stats['total_bills_ever'] += 1

                # Count by status
                status = bill_data.get('status', '').lower()
                if status in ['active', 'introduced', 'pending']:
                    stats['total_active'] += 1
                elif status in ['passed', 'signed', 'enacted']:
                    stats['total_passed'] += 1
                elif status in ['failed', 'rejected', 'defeated']:
                    stats['total_failed'] += 1
                elif status in ['withdrawn', 'suspended']:
                    stats['total_withdrawn'] += 1

                # Track access counts
                access_count = bill_data.get('access_count', 0)
                total_access_count += access_count

                if access_count > max_access_count:
                    max_access_count = access_count
                    most_accessed_title = bill_data.get(
                        'title', 'Unknown')[:50] + "..."

        stats['most_accessed_bill'] = most_accessed_title
        stats['avg_access_count'] = round(
            total_access_count / max(stats['total_bills_ever'], 1), 1)

    except Exception as e:
        print(f"Error calculating comprehensive statistics: {e}")

    return stats


@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "service": "truth-engine"}
