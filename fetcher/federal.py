import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

PROPUBLICA_API_KEY = os.getenv("PROPUBLICA_API_KEY")
BASE_URL = "https://api.propublica.org/congress/v1/bills/introduced.json"


def fetch_recent_federal_bills(limit=5):
    # If no API key, use mock data
    if not PROPUBLICA_API_KEY:
        print("No ProPublica API key found, using mock federal bills...")
        return get_mock_federal_bills()

    headers = {"X-API-Key": PROPUBLICA_API_KEY}
    response = requests.get(BASE_URL, headers=headers)
    if response.status_code != 200:
        print("Error fetching bills:", response.status_code)
        print("Using mock federal bills as fallback...")
        return get_mock_federal_bills()

    data = response.json()
    bills = data.get("results", [])[0].get("bills", [])
    return bills[:limit]


def get_mock_federal_bills():
    """Mock federal bills for testing when API is unavailable"""
    return [
        {
            "title": "Infrastructure Investment and Jobs Act Amendment",
            "summary": "A bill to amend the Infrastructure Investment and Jobs Act to extend funding for rural broadband initiatives and improve digital equity in underserved communities.",
            "sponsor": "Sen. Amy Klobuchar (D-MN)"
        },
        {
            "title": "Climate Resilience Act of 2025",
            "summary": "A bill to establish federal standards for climate adaptation and resilience planning in coastal communities threatened by rising sea levels.",
            "sponsor": "Rep. Alexandria Ocasio-Cortez (D-NY)"
        },
        {
            "title": "Small Business Relief Extension Act",
            "summary": "A bill to extend COVID-19 relief programs for small businesses through 2025, including forgivable loans and tax credits.",
            "sponsor": "Sen. Marco Rubio (R-FL)"
        },
        {
            "title": "Educational Technology Enhancement Act",
            "summary": "A bill to provide federal grants to schools for improving digital learning infrastructure and comprehensive teacher training programs.",
            "sponsor": "Rep. Bobby Scott (D-VA)"
        },
        {
            "title": "Veterans Healthcare Expansion Act",
            "summary": "A bill to expand mental health services and telehealth options for veterans in rural areas, including funding for mobile clinics.",
            "sponsor": "Sen. Jon Tester (D-MT)"
        }
    ]
