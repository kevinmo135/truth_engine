import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()


def fetch_recent_florida_bills():
    """
    Fetch recent Florida bills - currently using mock data
    Future implementation will scrape from:
    - https://www.myfloridahouse.gov/
    - https://www.flsenate.gov/
    """
    print("Fetching Florida bills... (placeholder)")
    return get_mock_florida_bills()


def get_mock_florida_bills():
    """Mock Florida bills with source URLs"""
    return [
        {
            "title": "Florida Education Freedom Act",
            "summary": "A bill to expand educational choice by creating universal education savings accounts for all K-12 students, allowing parents to use public funds for private schools, tutoring, and educational materials.",
            "sponsor": "Sen. Jennifer Bradley (R-FL)",
            "source_url": "https://www.flsenate.gov/Session/Bill/2025/1001",
            "source": "florida_senate"
        },
        {
            "title": "Campus Free Expression Protection Act",
            "summary": "A bill to protect free speech on university campuses by requiring public universities to remain neutral on controversial topics and prohibiting restrictions on guest speakers.",
            "sponsor": "Rep. Alex Andrade (R-FL)",
            "source_url": "https://www.myfloridahouse.gov/Sections/Bills/billsdetail.aspx?BillId=2025",
            "source": "florida_house"
        }
    ]
