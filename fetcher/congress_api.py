import requests
from typing import Dict, List, Optional
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()


class CongressAPI:
    """
    Congress.gov API client for fetching federal bills
    """

    def __init__(self):
        self.api_key = os.getenv('CONGRESS_API_KEY')
        if not self.api_key:
            raise ValueError(
                "CONGRESS_API_KEY environment variable is required")

        self.base_url = "https://api.congress.gov/v3"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Truth-Engine/1.0',
            'Accept': 'application/json'
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

    def get_recent_bills(self, limit: int = 1000) -> List[Dict]:
        """
        Get recent federal bills from Congress.gov
        """
        try:
            # Get bills from current congress (119th) - increased limit for comprehensive coverage
            response = self._make_request('bill', {
                'congress': '119',
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

            # Parse status from last action
            bill_status = self._parse_bill_status(last_action)

            # Format the bill number properly for display
            formatted_bill_number = self._format_bill_number(
                bill_type, bill_number)

            # Extract summary with improved logic
            extracted_summary = self._extract_bill_summary(
                bill_summary, title, bill_type, bill_number)

            return {
                'title': title,
                'summary': extracted_summary,
                'sponsor': sponsor_info,
                'source_url': source_url,
                'source': 'federal',
                'bill_id': f"{bill_type}{bill_number}",
                'bill_number': formatted_bill_number,  # Properly formatted number
                'state': 'US',
                'session': f"{congress}th Congress",
                'status': bill_status,
                'last_action': last_action,
                'last_action_date': last_action_date
            }

        except Exception as e:
            print(f"❌ Failed to process bill details: {e}")
            return None

    def _extract_bill_summary(self, bill_summary: Dict, title: str, bill_type: str, bill_number: str) -> str:
        """
        Extract bill summary with improved logic to avoid generic summaries
        """
        # Try to get the actual summary text
        summary_obj = bill_summary.get('summary', {})
        if isinstance(summary_obj, dict):
            summary_text = summary_obj.get('text', '').strip()
        else:
            summary_text = str(summary_obj).strip() if summary_obj else ''

        # If we have a meaningful summary, use it
        if summary_text and len(summary_text) > 20:
            # Check if it's not just a generic description
            if not summary_text.lower().startswith(f"federal legislation {bill_type.lower()}"):
                return summary_text

        # Fallback: try using the title as a more descriptive summary
        if title and len(title) > 10:
            # If title is descriptive enough, use it
            return title

        # Last resort: generic summary
        return f"Federal legislation {bill_type.upper()} {bill_number}"

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

    def _parse_bill_status(self, last_action: str) -> str:
        """
        Parse federal bill status from last action text
        """
        action_lower = last_action.lower()

        # Check for passed/enacted status (most definitive first)
        passed_indicators = [
            'became public law',
            'signed by president',
            'presented to president',
            'enrolled bill signed',
            'public law no.',
            'passed house and senate',
            'passed both chambers',
            'passed congress',
            'resolution agreed to in house and senate',
            'concurrent resolution agreed to',
            'joint resolution passed',
            'passed house',
            'passed senate',
            'passed/agreed to in house',
            'passed/agreed to in senate',
            'measure passed house',
            'measure passed senate',
            'bill passed',
            'resolution agreed to',
            'agreed to in house',
            'agreed to in senate'
        ]

        for indicator in passed_indicators:
            if indicator in action_lower:
                return 'passed'

        # Check for failed/dead status
        failed_indicators = [
            'failed',
            'defeated',
            'rejected',
            'died in committee',
            'killed',
            'withdrawn by sponsor',
            'motion to reconsider laid on the table',
            'cloture motion withdrawn',
            'motion to proceed withdrawn',
            'failed to pass',
            'motion failed',
            'amendment rejected',
            'bill failed'
        ]

        for indicator in failed_indicators:
            if indicator in action_lower:
                return 'failed'

        # Check for vetoed status
        veto_indicators = [
            'vetoed',
            'pocket vetoed',
            'returned without approval',
            'veto message received'
        ]

        for indicator in veto_indicators:
            if indicator in action_lower:
                return 'failed'  # Treating vetoed bills as failed for simplicity

        # Everything else is considered active
        return 'active'

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


def fetch_recent_federal_bills(limit: int = None) -> List[Dict]:
    """
    Fetch recent federal bills using Congress.gov API
    Returns all available recent bills (no limit unless specified)
    """
    print("🏛️ Fetching federal bills from Congress.gov...")

    try:
        api = CongressAPI()
        # Get ALL available bills for comprehensive coverage
        # Get comprehensive coverage
        bills = api.get_recent_bills(limit=limit or 1000)

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
