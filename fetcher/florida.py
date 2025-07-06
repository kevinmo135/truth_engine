import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import time
import re
from datetime import datetime

load_dotenv()


def fetch_recent_florida_bills(limit=3):
    """
    Fetch recent Florida bills from both Senate and House websites
    Returns a list of bills with real data from Florida legislature
    """
    print("Fetching recent Florida bills...")

    bills = []

    # Try to fetch from Florida Senate
    try:
        senate_bills = fetch_florida_senate_bills(limit//2 + 1)
        bills.extend(senate_bills)
        print(f"✅ Fetched {len(senate_bills)} Florida Senate bills")
    except Exception as e:
        print(f"⚠️ Could not fetch Florida Senate bills: {e}")

    # Try to fetch from Florida House
    try:
        house_bills = fetch_florida_house_bills(limit//2 + 1)
        bills.extend(house_bills)
        print(f"✅ Fetched {len(house_bills)} Florida House bills")
    except Exception as e:
        print(f"⚠️ Could not fetch Florida House bills: {e}")

    # If we couldn't fetch real bills, return empty list
    if not bills:
        print("❌ Could not fetch any Florida bills, returning empty list")
        return []

    return bills[:limit]


def fetch_florida_senate_bills(limit=2):
    """
    Scrape recent bills from Florida Senate website
    """
    current_year = datetime.now().year
    base_url = f"https://www.flsenate.gov/Session/Bills/{current_year}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(base_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        bills = []

        # Look for bill rows in the bills table
        bill_rows = soup.find_all('tr', class_='billRow')[:limit]

        for row in bill_rows:
            try:
                # Extract bill number and title
                bill_link = row.find('a', href=re.compile(r'/Session/Bill/'))
                if not bill_link:
                    continue

                bill_number = bill_link.text.strip()
                bill_url = f"https://www.flsenate.gov{bill_link['href']}"

                # Get bill title from the row
                title_cell = row.find('td', class_='billTitle')
                title = title_cell.text.strip(
                ) if title_cell else f"Florida Senate Bill {bill_number}"

                # Get sponsor information
                sponsor_cell = row.find('td', class_='billSponsor')
                sponsor = sponsor_cell.text.strip() if sponsor_cell else "Unknown Sponsor"

                # Get summary from bill detail page
                summary = get_bill_summary(bill_url, headers)

                bills.append({
                    'title': f"FL-S{bill_number}: {title}",
                    'summary': summary,
                    'sponsor': sponsor,
                    'source_url': bill_url,
                    'source': 'florida_senate'
                })

                time.sleep(0.5)  # Be respectful to the server

            except Exception as e:
                print(f"⚠️ Error parsing Senate bill row: {e}")
                continue

        return bills

    except Exception as e:
        print(f"❌ Error fetching Florida Senate bills: {e}")
        return []


def fetch_florida_house_bills(limit=2):
    """
    Scrape recent bills from Florida House website
    """
    # Florida House has a more complex search system, so we'll use a different approach
    current_year = datetime.now().year
    base_url = f"https://www.myfloridahouse.gov/Sections/Bills/bills.aspx?SessionId={current_year}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(base_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        bills = []

        # Look for bill links in the page
        bill_links = soup.find_all(
            'a', href=re.compile(r'BillsDetail\.aspx'))[:limit]

        for link in bill_links:
            try:
                bill_number = link.text.strip()
                bill_url = f"https://www.myfloridahouse.gov{link['href']}"

                # Get bill details from the detail page
                bill_details = get_house_bill_details(bill_url, headers)

                if bill_details:
                    bills.append({
                        'title': f"FL-H{bill_number}: {bill_details['title']}",
                        'summary': bill_details['summary'],
                        'sponsor': bill_details['sponsor'],
                        'source_url': bill_url,
                        'source': 'florida_house'
                    })

                time.sleep(0.5)  # Be respectful to the server

            except Exception as e:
                print(f"⚠️ Error parsing House bill: {e}")
                continue

        return bills

    except Exception as e:
        print(f"❌ Error fetching Florida House bills: {e}")
        return []


def get_bill_summary(bill_url, headers):
    """
    Get detailed summary from a Florida Senate bill page
    """
    try:
        response = requests.get(bill_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Look for bill summary in various possible locations
        summary_div = soup.find('div', class_='billSummary')
        if summary_div:
            return summary_div.text.strip()

        # Alternative: look for description
        desc_div = soup.find('div', class_='billDescription')
        if desc_div:
            return desc_div.text.strip()

        # Fallback: look for any paragraph with summary text
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            text = p.text.strip()
            if len(text) > 50 and any(keyword in text.lower() for keyword in ['relating to', 'an act', 'bill to']):
                return text

        return "Summary not available"

    except Exception as e:
        print(f"⚠️ Error fetching bill summary: {e}")
        return "Summary not available"


def get_house_bill_details(bill_url, headers):
    """
    Get detailed information from a Florida House bill page
    """
    try:
        response = requests.get(bill_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract title
        title_elem = soup.find('h1') or soup.find('h2')
        title = title_elem.text.strip() if title_elem else "Florida House Bill"

        # Extract sponsor
        sponsor_elem = soup.find(
            'span', string=re.compile(r'Sponsor|Primary Sponsor'))
        sponsor = "Unknown Sponsor"
        if sponsor_elem:
            sponsor_parent = sponsor_elem.parent
            sponsor = sponsor_parent.text.replace(
                'Sponsor:', '').replace('Primary Sponsor:', '').strip()

        # Extract summary
        summary_elem = soup.find('div', class_='billSummary') or soup.find(
            'div', id='billSummary')
        summary = summary_elem.text.strip() if summary_elem else "Summary not available"

        return {
            'title': title,
            'summary': summary,
            'sponsor': sponsor
        }

    except Exception as e:
        print(f"⚠️ Error fetching House bill details: {e}")
        return None


def get_mock_florida_bills():
    """Mock Florida bills - no longer used"""
    return []
