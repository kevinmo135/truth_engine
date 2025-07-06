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
    json_path = "data/latest_digest.json"

    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            data = json.load(f)
        reports = data.get('reports', [])
        generated_at = data.get('generated_at', 'Unknown')
    else:
        reports = []
        generated_at = "No data available"

    # Filter bills by status and source
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
        if status in ['passed', 'signed', 'enacted']:
            if is_federal:
                passed_federal.append(bill)
            else:
                passed_state.append(bill)
        elif status in ['failed', 'defeated', 'killed', 'died', 'vetoed']:
            if is_federal:
                failed_federal.append(bill)
            else:
                failed_state.append(bill)
        else:  # active, filed, referred, etc.
            if is_federal:
                active_federal.append(bill)
            else:
                active_state.append(bill)

    # Sort all bill categories by popularity (most popular first)
    active_federal = sort_bills_by_popularity(active_federal)
    passed_federal = sort_bills_by_popularity(passed_federal)
    failed_federal = sort_bills_by_popularity(failed_federal)
    active_state = sort_bills_by_popularity(active_state)
    passed_state = sort_bills_by_popularity(passed_state)
    failed_state = sort_bills_by_popularity(failed_state)

    # Apply initial limit to show first 100 bills total
    # Show up to 50 federal bills initially
    initial_federal = active_federal[:limit//2]
    # Show up to 50 state bills initially
    initial_state = active_state[:limit//2]

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "reports": reports,  # Keep for backwards compatibility
        "active_federal": initial_federal,
        # Show fewer passed/failed initially
        "passed_federal": passed_federal[:20],
        "failed_federal": failed_federal[:10],
        "active_state": initial_state,
        "passed_state": passed_state[:20],
        "failed_state": failed_state[:10],
        "generated_at": generated_at,
        "total_bills": len(reports),
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
    """Analytics dashboard showing trends and insights"""
    json_path = "data/latest_digest.json"

    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            data = json.load(f)
        reports = data.get('reports', [])
        generated_at = data.get('generated_at', 'Unknown')

        # Generate analytics report
        analytics_data = generate_analytics_report(reports)

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

        # Filter bills by status and source
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
            if status in ['passed', 'signed', 'enacted']:
                if is_federal:
                    passed_federal.append(bill)
                else:
                    passed_state.append(bill)
            elif status in ['failed', 'defeated', 'killed', 'died', 'vetoed']:
                if is_federal:
                    failed_federal.append(bill)
                else:
                    failed_state.append(bill)
            else:  # active, filed, referred, etc.
                if is_federal:
                    active_federal.append(bill)
                else:
                    active_state.append(bill)

        # Sort all bill categories by popularity (most popular first)
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


@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "service": "truth-engine"}
