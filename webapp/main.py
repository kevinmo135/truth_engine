from analyzer.summary import get_detailed_analysis
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


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Main dashboard showing all bills"""
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

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "reports": reports,  # Keep for backwards compatibility
        "active_federal": active_federal,
        "passed_federal": passed_federal,
        "failed_federal": failed_federal,
        "active_state": active_state,
        "passed_state": passed_state,
        "failed_state": failed_state,
        "generated_at": generated_at,
        "total_bills": len(reports)
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


@app.get("/api/bills")
async def get_bills_api():
    """API endpoint for bills data"""
    json_path = "data/latest_digest.json"

    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            return json.load(f)
    else:
        return {"error": "No data available"}


@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "service": "truth-engine"}
