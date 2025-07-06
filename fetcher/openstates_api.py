import requests
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional
import time

load_dotenv()


class OpenStatesAPI:
    """
    Open States API v3 integration for fetching state legislative data
    """

    def __init__(self):
        self.api_key = os.getenv('OPENSTATES_API_KEY')
        if not self.api_key:
            print("⚠️ OPENSTATES_API_KEY not found - some functionality may be limited")

        self.base_url = "https://v3.openstates.org"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TruthEngine/1.0',
            'Accept': 'application/json'
        })

        if self.api_key:
            self.session.headers.update({
                'X-API-KEY': self.api_key
            })

    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """
        Make request to Open States API v3
        """
        if params is None:
            params = {}

        try:
            response = self.session.get(
                f"{self.base_url}/{endpoint}", params=params)
            response.raise_for_status()

            data = response.json()
            return data

        except requests.exceptions.RequestException as e:
            print(f"❌ Open States API request failed: {e}")
            raise

    def get_bills_by_state(self, state: str, session: str = None, limit: int = 20) -> List[Dict]:
        """
        Get bills for a specific state using Open States API v3

        Args:
            state: State abbreviation (e.g., 'fl' for Florida)
            session: Legislative session (e.g., '2024' or '2025')
            limit: Maximum number of bills to return
        """
        try:
            # Build jurisdiction parameter (state abbreviation to full name mapping)
            jurisdiction_map = {
                'fl': 'Florida',
                'ca': 'California',
                'tx': 'Texas',
                'ny': 'New York',
                # Add more as needed
            }

            jurisdiction = jurisdiction_map.get(state.lower(), state.title())

            params = {
                'jurisdiction': jurisdiction,
                'per_page': min(limit, 100),  # API limits to 100 per page
                'sort': 'updated_at'
            }

            if session:
                params['session'] = session

            response = self._make_request('bills', params)

            bills = []
            bill_data = response.get('results', [])

            for bill in bill_data:
                # Transform to our standard format
                bill_detail = self._transform_bill_data(bill, state)
                if bill_detail:
                    bills.append(bill_detail)

            return bills

        except Exception as e:
            print(f"❌ Failed to fetch bills from Open States: {e}")
            return []

    def _transform_bill_data(self, bill_data: Dict, state: str) -> Optional[Dict]:
        """
        Transform Open States v3 bill data to our standard format
        """
        try:
            # Get basic info
            title = bill_data.get('title', '')
            bill_id = bill_data.get('identifier', '')

            # Get session info
            session_data = bill_data.get('session', {})
            session = session_data.get(
                'identifier', '') if session_data else ''

            # Get sponsor information
            sponsorships = bill_data.get('sponsorships', [])
            primary_sponsor = self._extract_primary_sponsor(sponsorships)

            # Get summary/abstract
            abstracts = bill_data.get('abstracts', [])
            summary = ''
            if abstracts:
                summary = abstracts[0].get('abstract', '')

            if not summary:
                summary = f"{state.upper()} legislation {bill_id} - {title[:100]}"

            # Get source URLs - use openstates_url if available
            source_url = bill_data.get('openstates_url', '')
            if not source_url:
                # Try to get from sources
                sources = bill_data.get('sources', [])
                if sources:
                    source_url = sources[0].get('url', '')

            # Get latest action
            actions = bill_data.get('actions', [])
            last_action = 'No action recorded'
            last_action_date = ''
            if actions:
                latest = actions[-1]
                last_action = latest.get('description', 'No action recorded')
                last_action_date = latest.get('date', '')

            return {
                'title': title,
                'summary': summary,
                'sponsor': primary_sponsor,
                'source_url': source_url,
                'source': state.lower(),
                'bill_id': bill_id,
                'state': state.upper(),
                'session': session,
                'status': last_action,
                'last_action': last_action,
                'last_action_date': last_action_date
            }

        except Exception as e:
            print(f"❌ Failed to transform bill data: {e}")
            return None

    def _extract_primary_sponsor(self, sponsorships: List[Dict]) -> str:
        """
        Extract primary sponsor from sponsorships list
        """
        if not sponsorships:
            return "Unknown"

        # Look for primary sponsor first
        primary_sponsor = next(
            (s for s in sponsorships if s.get('primary', False)),
            sponsorships[0] if sponsorships else None
        )

        if not primary_sponsor:
            return "Unknown"

        # Get person data
        person_data = primary_sponsor.get('person')
        if person_data:
            name = person_data.get('name', 'Unknown')
            # Try to extract party from current memberships
            current_memberships = person_data.get('current_memberships', [])
            party = ''
            for membership in current_memberships:
                org = membership.get('organization', {})
                if org.get('classification') == 'party':
                    party = org.get('name', '')
                    break

            if party:
                return f"{name} ({party})"
            else:
                return name

        return "Unknown"


def fetch_recent_florida_bills(limit: int = 3) -> List[Dict]:
    """
    Fetch recent Florida bills using Open States API v3
    """
    print("🌴 Fetching Florida bills from Open States API v3...")

    try:
        api = OpenStatesAPI()
        if not api.api_key:
            print("❌ OPENSTATES_API_KEY not set - cannot fetch data")
            print("🔧 Get an API key from: https://openstates.org/accounts/profile/")
            return []

        bills = api.get_bills_by_state(
            state='fl',
            session='2025',  # Current session
            limit=limit
        )

        # Add source type for consistency
        for bill in bills:
            bill['source'] = 'florida'

        print(f"✅ Successfully fetched {len(bills)} Florida bills")
        return bills

    except Exception as e:
        print(f"❌ Failed to fetch Florida bills: {e}")
        print("🚫 No fallback data - returning empty list")
        return []


def fetch_bills_by_state(state: str, session: str = None, limit: int = 5) -> List[Dict]:
    """
    Fetch bills for any state using Open States API v3
    """
    print(f"📊 Fetching {state.upper()} bills from Open States API v3...")

    try:
        api = OpenStatesAPI()
        if not api.api_key:
            print("❌ OPENSTATES_API_KEY not set - cannot fetch data")
            return []

        bills = api.get_bills_by_state(
            state=state,
            session=session,
            limit=limit
        )

        # Add source type
        for bill in bills:
            bill['source'] = state.lower()

        print(f"✅ Successfully fetched {len(bills)} {state.upper()} bills")
        return bills

    except Exception as e:
        print(f"❌ Failed to fetch {state.upper()} bills: {e}")
        return []
