import requests
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional
import time

load_dotenv()


class CongressAPI:
    """
    Congress.gov API integration for fetching federal legislative data
    """

    def __init__(self):
        self.api_key = os.getenv('CONGRESS_API_KEY')
        if not self.api_key:
            raise ValueError("CONGRESS_API_KEY environment variable not set")

        self.base_url = "https://api.congress.gov/v3"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TruthEngine/1.0',
            'Accept': 'application/json',
            'X-API-Key': self.api_key
        })

    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """
        Make authenticated request to Congress.gov API
        """
        if params is None:
            params = {}

        params['api_key'] = self.api_key

        try:
            response = self.session.get(
                f"{self.base_url}/{endpoint}", params=params)
            response.raise_for_status()

            data = response.json()
            return data

        except requests.exceptions.RequestException as e:
            print(f"❌ Congress.gov API request failed: {e}")
            raise

    def get_recent_bills(self, limit: int = 20) -> List[Dict]:
        """
        Get recent federal bills from Congress.gov
        """
        try:
            # Get bills from current congress (118th)
            response = self._make_request('bill', {
                'congress': '118',
                'limit': limit,
                'sort': 'updateDate+desc'
            })

            bills = []
            bill_data = response.get('bills', [])

            for bill in bill_data:
                # Get detailed bill information
                bill_detail = self.get_bill_details(bill)
                if bill_detail:
                    bills.append(bill_detail)

            return bills

        except Exception as e:
            print(f"❌ Failed to fetch bills from Congress.gov: {e}")
            return []

    def get_bill_details(self, bill_summary: Dict) -> Optional[Dict]:
        """
        Transform Congress.gov bill data to our standard format
        """
        try:
            # Extract basic info
            bill_type = bill_summary.get('type', '').lower()
            bill_number = bill_summary.get('number', '')
            congress = bill_summary.get('congress', '118')

            # Get title and summary
            title = bill_summary.get('title', '')
            if not title:
                title = f"{bill_type.upper()} {bill_number}"

            # Get sponsor information
            sponsor_info = self._extract_sponsor(
                bill_summary.get('sponsors', []))

            # Build Congress.gov URL with proper bill type mapping
            bill_type_map = {
                'hr': 'house-bill',
                's': 'senate-bill',
                'hjres': 'house-joint-resolution',
                'sjres': 'senate-joint-resolution',
                'hconres': 'house-concurrent-resolution',
                'sconres': 'senate-concurrent-resolution',
                'hres': 'house-resolution',
                'sres': 'senate-resolution'
            }

            bill_type_clean = bill_type.replace('.', '').lower()
            url_bill_type = bill_type_map.get(
                bill_type_clean, f"{bill_type_clean}-bill")
            source_url = f"https://www.congress.gov/bill/{congress}th-congress/{url_bill_type}/{bill_number}"

            # Get latest action
            latest_action = bill_summary.get('latestAction', {})
            last_action = latest_action.get('text', 'No action recorded')
            last_action_date = latest_action.get('actionDate', '')

            # Format the bill number properly for display
            formatted_bill_number = self._format_bill_number(
                bill_type, bill_number)

            return {
                'title': title,
                'summary': bill_summary.get('summary', {}).get('text', f"Federal legislation {bill_type.upper()} {bill_number}"),
                'sponsor': sponsor_info,
                'source_url': source_url,
                'source': 'federal',
                'bill_id': f"{bill_type}{bill_number}",
                'bill_number': formatted_bill_number,  # Properly formatted number
                'state': 'US',
                'session': f"{congress}th Congress",
                'status': last_action,
                'last_action': last_action,
                'last_action_date': last_action_date
            }

        except Exception as e:
            print(f"❌ Failed to process bill details: {e}")
            return None

    def _extract_sponsor(self, sponsors: List[Dict]) -> str:
        """
        Extract primary sponsor from sponsors list
        """
        if not sponsors:
            return "Unknown"

        # Get the first sponsor (primary)
        primary_sponsor = sponsors[0]

        first_name = primary_sponsor.get('firstName', '')
        last_name = primary_sponsor.get('lastName', '')
        party = primary_sponsor.get('party', '')
        state = primary_sponsor.get('state', '')

        name = f"{first_name} {last_name}".strip()
        if not name:
            name = primary_sponsor.get('fullName', 'Unknown')

        # Format: "Sen. John Smith (R-TX)" or "Rep. Jane Doe (D-CA)"
        title = "Sen." if primary_sponsor.get('isSenator') else "Rep."

        if party and state:
            return f"{title} {name} ({party}-{state})"
        elif party:
            return f"{title} {name} ({party})"
        else:
            return f"{title} {name}"

    def _format_bill_number(self, bill_type: str, bill_number: str) -> str:
        """
        Format bill number for proper display (e.g., H.R.618, S.1234)
        """
        bill_type_clean = bill_type.replace('.', '').lower()

        # Map bill types to proper display format
        bill_type_map = {
            'hr': 'H.R.',
            's': 'S.',
            'hjres': 'H.J.Res.',
            'sjres': 'S.J.Res.',
            'hconres': 'H.Con.Res.',
            'sconres': 'S.Con.Res.',
            'hres': 'H.Res.',
            'sres': 'S.Res.'
        }

        formatted_type = bill_type_map.get(bill_type_clean, bill_type.upper())
        return f"{formatted_type}{bill_number}"


def fetch_recent_federal_bills(limit: int = 50) -> List[Dict]:
    """
    Fetch recent federal bills using Congress.gov API
    Returns more bills than before (up to 50 recent bills)
    """
    print("🏛️ Fetching federal bills from Congress.gov...")

    try:
        api = CongressAPI()
        # Get more bills to provide better coverage of recent legislation
        bills = api.get_recent_bills(limit=50)  # Increased from 5 to 50

        print(f"✅ Successfully fetched {len(bills)} federal bills")
        print(f"📋 Recent Federal Bills:")
        for i, bill in enumerate(bills[:10], 1):  # Show first 10 in summary
            print(
                f"   {i}. {bill.get('bill_number', 'N/A')}: {bill.get('title', 'N/A')[:50]}...")
        if len(bills) > 10:
            print(f"   ... and {len(bills) - 10} more bills")

        return bills

    except Exception as e:
        print(f"❌ Failed to fetch federal bills: {e}")
        print("🚫 No fallback data - returning empty list")
        return []


def fetch_recent_florida_bills(limit: int = 3) -> List[Dict]:
    """
    Florida bills - currently disabled until we find a good API
    """
    print("🌴 Florida bills currently disabled - no suitable API found")
    return []
