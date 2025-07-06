import requests
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional
import time

load_dotenv()


class LegiScanAPI:
    """
    LegiScan API integration for fetching both federal and state legislative data
    """

    def __init__(self):
        self.api_key = os.getenv('LEGISCAN_API_KEY')
        if not self.api_key:
            raise ValueError("LEGISCAN_API_KEY environment variable not set")

        self.base_url = "https://api.legiscan.com/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TruthEngine/1.0',
            'Accept': 'application/json'
        })

    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """
        Make authenticated request to LegiScan API
        """
        if params is None:
            params = {}

        params['key'] = self.api_key

        try:
            response = self.session.get(
                f"{self.base_url}{endpoint}", params=params)
            response.raise_for_status()

            data = response.json()

            # Check for API errors
            if data.get('status') == 'ERROR':
                raise Exception(
                    f"LegiScan API Error: {data.get('alert', 'Unknown error')}")

            return data
        except requests.exceptions.RequestException as e:
            print(f"❌ LegiScan API request failed: {e}")
            raise

    def get_bill_list(self, state: str = None, year: int = None, limit: int = 50) -> List[Dict]:
        """
        Get list of bills from LegiScan

        Args:
            state: State abbreviation (e.g., 'FL' for Florida, 'US' for federal)
            year: Year to search (defaults to current year)
            limit: Maximum number of bills to return
        """
        params = {}

        if state:
            params['state'] = state
        if year:
            params['year'] = year

        try:
            # LegiScan typically uses getBillList or similar endpoint
            response = self._make_request('getBillList', params)

            bills = []
            bill_data = response.get('bills', [])

            for bill in bill_data[:limit]:
                # Get detailed bill information
                bill_detail = self.get_bill_details(bill.get('bill_id'))
                if bill_detail:
                    bills.append(bill_detail)

            return bills

        except Exception as e:
            print(f"❌ Failed to fetch bills from LegiScan: {e}")
            return []

    def get_bill_details(self, bill_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific bill
        """
        try:
            response = self._make_request('getBill', {'id': bill_id})

            bill_data = response.get('bill', {})

            # Transform LegiScan format to our standard format
            return {
                'title': bill_data.get('title', ''),
                'summary': bill_data.get('description', ''),
                'sponsor': self._extract_sponsor(bill_data.get('sponsors', [])),
                'source_url': bill_data.get('state_link', ''),
                'source': 'legiscan',
                'bill_id': bill_data.get('bill_id', ''),
                'state': bill_data.get('state', ''),
                'session': bill_data.get('session', ''),
                'status': bill_data.get('status', ''),
                'last_action': bill_data.get('last_action', ''),
                'last_action_date': bill_data.get('last_action_date', '')
            }

        except Exception as e:
            print(f"❌ Failed to fetch bill details for {bill_id}: {e}")
            return None

    def _extract_sponsor(self, sponsors: List[Dict]) -> str:
        """
        Extract primary sponsor from sponsors list
        """
        if not sponsors:
            return "Unknown"

        # Find primary sponsor or use first one
        primary_sponsor = next(
            (s for s in sponsors if s.get('sponsor_type_id') == 1), sponsors[0])

        name = primary_sponsor.get('name', 'Unknown')
        party = primary_sponsor.get('party', '')

        if party:
            return f"{name} ({party})"
        return name

    def search_bills(self, query: str, state: str = None, limit: int = 50) -> List[Dict]:
        """
        Search for bills by keyword
        """
        params = {'q': query}

        if state:
            params['state'] = state

        try:
            response = self._make_request('getSearch', params)

            bills = []
            results = response.get('searchresult', [])

            for result in results[:limit]:
                bill_detail = self.get_bill_details(result.get('bill_id'))
                if bill_detail:
                    bills.append(bill_detail)

            return bills

        except Exception as e:
            print(f"❌ Failed to search bills: {e}")
            return []


def fetch_recent_federal_bills(limit: int = 5) -> List[Dict]:
    """
    Fetch recent federal bills using LegiScan API
    """
    print("🏛️ Fetching federal bills from LegiScan...")

    try:
        api = LegiScanAPI()
        bills = api.get_bill_list(state='US', limit=limit)

        # Add source type for consistency
        for bill in bills:
            bill['source'] = 'federal'

        print(f"✅ Successfully fetched {len(bills)} federal bills")
        return bills

    except Exception as e:
        print(f"❌ Failed to fetch federal bills: {e}")
        print("🚫 No mock data - returning empty list")
        return []


def fetch_recent_florida_bills(limit: int = 3) -> List[Dict]:
    """
    Fetch recent Florida bills using LegiScan API
    """
    print("🌴 Fetching Florida bills from LegiScan...")

    try:
        api = LegiScanAPI()
        bills = api.get_bill_list(state='FL', limit=limit)

        # Add source type for consistency
        for bill in bills:
            bill['source'] = 'florida'

        print(f"✅ Successfully fetched {len(bills)} Florida bills")
        return bills

    except Exception as e:
        print(f"❌ Failed to fetch Florida bills: {e}")
        print("🚫 No mock data - returning empty list")
        return []


# Legacy compatibility functions
def fetch_recent_bills_by_state(state: str, limit: int = 5) -> List[Dict]:
    """
    Fetch recent bills for any state using LegiScan API
    """
    print(f"🔍 Fetching bills for {state} from LegiScan...")

    try:
        api = LegiScanAPI()
        bills = api.get_bill_list(state=state, limit=limit)

        # Add source type
        for bill in bills:
            bill['source'] = state.lower()

        print(f"✅ Successfully fetched {len(bills)} bills for {state}")
        return bills

    except Exception as e:
        print(f"❌ Failed to fetch bills for {state}: {e}")
        return []


def search_bills_by_topic(topic: str, state: str = None, limit: int = 10) -> List[Dict]:
    """
    Search for bills by topic across states
    """
    print(f"🔍 Searching for bills about '{topic}'...")

    try:
        api = LegiScanAPI()
        bills = api.search_bills(topic, state=state, limit=limit)

        print(f"✅ Found {len(bills)} bills about '{topic}'")
        return bills

    except Exception as e:
        print(f"❌ Failed to search bills: {e}")
        return []
