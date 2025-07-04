import requests
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def fetch_recent_federal_bills(limit=5):
    """
    Fetch recent federal bills from congress.gov API
    Now with API key support and source URLs
    """
    api_key = os.getenv("CONGRESS_API_KEY")

    if not api_key:
        print("No Congress.gov API key found, using mock data...")
        return get_mock_federal_bills()

    # Get bills from the last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    url = "https://api.congress.gov/v3/bill"
    params = {
        'api_key': api_key,
        'format': 'json',
        'limit': limit,
        'fromDateTime': start_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'toDateTime': end_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'sort': 'updateDate+desc'
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            bills = []

            for bill_data in data.get('bills', [])[:limit]:
                bill = {
                    'title': bill_data.get('title', 'Unknown Title'),
                    'summary': bill_data.get('summary', {}).get('text', 'No summary available'),
                    'sponsor': extract_sponsor(bill_data),
                    'source_url': f"https://www.congress.gov/bill/{bill_data.get('congress', 'unknown')}/{bill_data.get('type', 'unknown')}/{bill_data.get('number', 'unknown')}",
                    'source': 'congress.gov'
                }
                bills.append(bill)

            if bills:
                print(
                    f"Successfully fetched {len(bills)} federal bills from Congress.gov")
                return bills
            else:
                print("No bills found, using mock data...")
                return get_mock_federal_bills()
        else:
            print(
                f"Congress.gov API returned status code: {response.status_code}")
            print("Using mock federal bills as fallback...")
            return get_mock_federal_bills()

    except Exception as e:
        print(f"Error fetching from Congress.gov: {e}")
        print("Using mock federal bills as fallback...")
        return get_mock_federal_bills()


def extract_sponsor(bill_data):
    """Extract sponsor information from bill data"""
    sponsors = bill_data.get('sponsors', [])
    if sponsors:
        sponsor = sponsors[0]
        name = sponsor.get('fullName', 'Unknown')
        party = sponsor.get('party', '')
        state = sponsor.get('state', '')

        if party and state:
            return f"{name} ({party}-{state})"
        elif party:
            return f"{name} ({party})"
        else:
            return name
    return "Unknown Sponsor"


def get_mock_federal_bills():
    """Fallback mock federal bills with source URLs"""
    return [
        {
            'title': 'Apex Area Technical Corrections Act',
            'summary': 'A bill to make technical corrections to the Apex Area Land Restoration Act of 2019.',
            'sponsor': 'Rep. Johnson (D-TX)',
            'source_url': 'https://www.congress.gov/bill/118th-congress/house-bill/1234',
            'source': 'mock_congress'
        },
        {
            'title': 'Alaska Native Village Municipal Lands Restoration Act',
            'summary': 'To provide for the restoration of municipal lands to Alaska Native villages.',
            'sponsor': 'Rep. Peltola (D-AK)',
            'source_url': 'https://www.congress.gov/bill/118th-congress/house-bill/5678',
            'source': 'mock_congress'
        },
        {
            'title': 'Alaska Native Settlement Trust Eligibility Act',
            'summary': 'To amend the Alaska Native Claims Settlement Act to clarify the eligibility of Native descendants.',
            'sponsor': 'Sen. Murkowski (R-AK)',
            'source_url': 'https://www.congress.gov/bill/118th-congress/senate-bill/9101',
            'source': 'mock_congress'
        },
        {
            'title': 'Salem Maritime National Historical Park Redesignation Act',
            'summary': 'To redesignate the Salem Maritime National Historic Site as Salem Maritime National Historical Park.',
            'sponsor': 'Rep. Moulton (D-MA)',
            'source_url': 'https://www.congress.gov/bill/118th-congress/house-bill/1121',
            'source': 'mock_congress'
        },
        {
            'title': 'One Big Beautiful Bill Act',
            'summary': 'An omnibus bill to address various legislative priorities including infrastructure, healthcare, and education funding.',
            'sponsor': 'Rep. Smith (D-CA)',
            'source_url': 'https://www.congress.gov/bill/118th-congress/house-bill/3141',
            'source': 'mock_congress'
        }
    ]
