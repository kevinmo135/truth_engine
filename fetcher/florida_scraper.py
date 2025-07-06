import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from typing import List, Dict, Optional
import time
import re
from urllib.parse import urljoin, urlparse

load_dotenv()


class FloridaBillScraper:
    """
    Direct web scraper for Florida legislature bills
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })

    def scrape_florida_bills_from_house_site(self, limit: int = 5) -> List[Dict]:
        """
        Scrape Florida bills from Florida House website
        (flhouse.gov has both House and Senate bills)
        """
        bills = []
        try:
            print("🏛️ Scraping Florida bills from flhouse.gov...")

            # Try different approaches to access the Florida House bills
            base_urls = [
                "https://www.flhouse.gov/Sections/Bills/bills.aspx?SessionId=105&HouseChamber=B",
                "https://www.flhouse.gov/Sections/Bills/bills.aspx?SessionId=105",
                "https://www.flhouse.gov/Sections/Bills/bills.aspx"
            ]

            for base_url in base_urls:
                try:
                    print(f"🔍 Trying URL: {base_url}")
                    response = self.session.get(base_url, timeout=15)

                    # Check if we got the rejection message
                    if "requested URL was rejected" in response.text.lower():
                        print(f"❌ URL rejected by server: {base_url}")
                        continue

                    response.raise_for_status()
                    soup = BeautifulSoup(response.content, 'html.parser')

                    # Look for bill links in various formats
                    bill_link_patterns = [
                        r'/Sections/Bills/billsdetail\.aspx\?BillId=\d+',
                        r'/Bills/billsdetail\.aspx\?.*BillId=\d+',
                        r'billsdetail\.aspx\?.*BillId=\d+'
                    ]

                    found_links = []
                    for pattern in bill_link_patterns:
                        links = soup.find_all('a', href=re.compile(pattern))
                        found_links.extend(links)

                    if found_links:
                        print(f"✅ Found {len(found_links)} bill links")
                        count = 0
                        processed = 0
                        # Process ALL bills (or as many as reasonable) to find the best active ones
                        # Process all 150 bills to ensure we don't miss important legislation
                        # Process ALL bills found
                        max_to_process = len(found_links)

                        print(
                            f"🔍 Processing ALL {max_to_process} bills to find active legislation...")

                        for link in found_links:
                            processed += 1
                            try:
                                bill_url = urljoin(base_url, link.get('href'))
                                bill_data = self._scrape_florida_house_bill_detail(
                                    bill_url)
                                if bill_data:
                                    bills.append(bill_data)
                                    count += 1
                                    print(
                                        f"✅ Found active bill {count}: {bill_data['bill_number']} - {bill_data['title'][:50]}...")
                                    # Be respectful to the server
                                    # Slightly faster but still respectful
                                    time.sleep(0.3)

                                # Print progress every 20 bills
                                if processed % 20 == 0:
                                    print(
                                        f"🔍 Processed {processed}/{max_to_process} bills, found {count} active bills")

                            except Exception as e:
                                print(
                                    f"⚠️ Failed to scrape bill from {bill_url}: {e}")
                                continue

                        print(
                            f"📊 FINAL: Processed {processed} bills, found {count} active bills total")

                        if bills:
                            break  # Found bills, no need to try other URLs

                except Exception as e:
                    print(f"⚠️ Failed to access {base_url}: {e}")
                    continue

            print(f"✅ Scraped {len(bills)} Florida bills from House site")

        except Exception as e:
            print(f"❌ Failed to scrape Florida House site: {e}")

        return bills

    def _scrape_florida_bill_detail(self, bill_url: str) -> Optional[Dict]:
        """
        Scrape individual Florida bill details (both House and Senate)
        """
        try:
            response = self.session.get(bill_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract bill number from URL
            bill_match = re.search(r'/Bill/(\d+)/(\d+)', bill_url)
            if not bill_match:
                return None

            year, bill_num = bill_match.groups()

            # Extract title first - prioritize elements with bill numbers
            raw_title = ""
            # Look for H2 elements first (they usually contain bill numbers)
            h2_elements = soup.find_all('h2')
            for elem in h2_elements:
                candidate_title = elem.get_text(strip=True)
                if candidate_title and re.search(r'(HB|SB)\s*\d+', candidate_title, re.IGNORECASE):
                    raw_title = candidate_title
                    break

            # If no H2 with bill number, try H1
            if not raw_title:
                h1_elements = soup.find_all('h1')
                for elem in h1_elements:
                    candidate_title = elem.get_text(strip=True)
                    if candidate_title and re.search(r'(HB|SB)\s*\d+', candidate_title, re.IGNORECASE):
                        raw_title = candidate_title
                        break

            # Fallback to first substantial title
            if not raw_title:
                title_elem = soup.find('h1') or soup.find('h2')
                raw_title = title_elem.get_text(
                    strip=True) if title_elem else f"Florida Bill {bill_num}"

            # Extract the REAL bill number from the title (not the URL ID)
            bill_number_match = re.search(
                r'^((?:CS/)*(?:HB|SB)\s*\d+)', raw_title, re.IGNORECASE)

            if bill_number_match:
                # Found real bill number in title
                real_bill_number = bill_number_match.group(1).strip()
                real_bill_number = re.sub(
                    r'\s+', ' ', real_bill_number.upper())

                # Determine chamber from the real bill number
                if 'HB' in real_bill_number:
                    chamber = "House"
                    sponsor_title = "Rep."
                    bill_type = "House"
                else:
                    chamber = "Senate"
                    sponsor_title = "Sen."
                    bill_type = "Senate"

                bill_id = real_bill_number
                bill_number = real_bill_number.replace(' ', '-')

                print(
                    f"📋 Extracted real bill number: {real_bill_number} from title")
            else:
                # Fallback to URL ID method
                page_text = soup.get_text().lower()
                is_house_bill = 'house bill' in page_text or 'hb' in page_text

                if is_house_bill:
                    bill_id = f"HB {bill_num}"
                    bill_number = f"HB-{bill_num}"
                    chamber = "House"
                    sponsor_title = "Rep."
                    bill_type = "House"
                else:
                    bill_id = f"SB {bill_num}"
                    bill_number = f"SB-{bill_num}"
                    chamber = "Senate"
                    sponsor_title = "Sen."
                    bill_type = "Senate"

            # Clean title by removing bill number from the beginning
            title = re.sub(r'^((?:CS/)*(?:SB|HB)\s*\d+):\s*', '',
                           raw_title, flags=re.IGNORECASE).strip()

            # If title is now empty or too short, use the raw title
            if not title or len(title) < 10:
                title = raw_title

            # Extract sponsor
            sponsor = "Unknown"
            sponsor_elem = soup.find(text=re.compile(r'by\s+', re.IGNORECASE))
            if sponsor_elem:
                sponsor_text = sponsor_elem.strip()
                sponsor_match = re.search(
                    r'by\s+([^;]+)', sponsor_text, re.IGNORECASE)
                if sponsor_match:
                    sponsor = f"{sponsor_title} {sponsor_match.group(1).strip()}"

            # Extract summary/description
            summary = ""

            # Look for bill description in various places
            desc_selectors = [
                'div.bill-summary',
                'div.summary',
                '.bill-text p',
                'td:contains("Summary")',
                'p'
            ]

            for selector in desc_selectors:
                if ':contains(' in selector:
                    # Handle pseudo-selector
                    elements = soup.find_all('td')
                    for elem in elements:
                        if 'summary' in elem.get_text().lower():
                            next_elem = elem.find_next_sibling()
                            if next_elem:
                                summary = next_elem.get_text(strip=True)
                                break
                else:
                    elem = soup.select_one(selector)
                    if elem:
                        text = elem.get_text(strip=True)
                        if len(text) > 50:  # Make sure it's substantial
                            summary = text
                            break

            # If no summary found, use title as summary
            if not summary:
                summary = f"Florida {bill_type} Bill {bill_num}: {title}"

            # Clean up summary
            summary = re.sub(r'\s+', ' ', summary)
            if len(summary) > 500:
                summary = summary[:500] + "..."

            # Check for completion status
            page_text_full = soup.get_text().lower()
            final_completion_patterns = [
                r'bill\s+(passed|failed|died|killed|defeated)',
                r'(signed into law|became law|enacted)',
                r'(vetoed|withdrawn)\s+(by|from)',
                r'final\s+(passage|vote|reading)\s+(passed|failed)',
                r'governor\s+(signed|vetoed)',
                r'(cs\s+passed|committee\s+substitute\s+passed)',
                r'status:\s*(passed|failed|died|enacted|signed|vetoed|withdrawn)'
            ]

            bill_is_completed = False
            completion_reason = None
            bill_status = "Active"

            for pattern in final_completion_patterns:
                match = re.search(pattern, page_text_full, re.IGNORECASE)
                if match:
                    bill_is_completed = True
                    completion_reason = match.group(0).lower()

                    # Determine the specific status
                    if any(word in completion_reason for word in ['passed', 'enacted', 'signed into law', 'became law']):
                        bill_status = "Passed"
                    elif any(word in completion_reason for word in ['failed', 'died', 'killed', 'defeated']):
                        bill_status = "Failed"
                    elif 'vetoed' in completion_reason:
                        bill_status = "Vetoed"
                    elif 'withdrawn' in completion_reason:
                        bill_status = "Withdrawn"
                    else:
                        bill_status = "Completed"
                    break

            # Only skip if it's clearly an old completed bill (no recent activity)
            if bill_is_completed:
                import datetime
                current_year = datetime.datetime.now().year

                # Check if there's recent activity (current or previous year)
                has_recent_activity = (str(current_year) in page_text_full or
                                       str(current_year - 1) in page_text_full or
                                       '2024' in page_text_full or '2025' in page_text_full)

                if not has_recent_activity:
                    print(
                        f"⏭️ Skipping old completed bill {bill_num} (reason: {completion_reason}, no recent activity)")
                    return None
                else:
                    print(
                        f"✅ Including recently completed bill {bill_num} (status: {bill_status}, reason: {completion_reason})")
            else:
                bill_status = "Active"
                print(
                    f"✅ Including active bill {bill_num} (status: {bill_status})")

            # Use the direct bill URL as the source URL
            return {
                'title': title,
                'summary': summary,
                'sponsor': sponsor,
                'source_url': bill_url,
                'source': 'florida',
                'bill_id': bill_id,
                'bill_number': bill_number,  # Properly formatted number
                'state': 'FL',
                'chamber': chamber,
                'session': year,
                'status': bill_status,
                'last_action': bill_status,
                'last_action_date': '',
                'completion_reason': completion_reason if bill_is_completed else None
            }

        except Exception as e:
            print(f"❌ Failed to scrape bill detail from {bill_url}: {e}")
            return None

    def _scrape_florida_house_bill_detail(self, bill_url: str) -> Optional[Dict]:
        """
        Scrape individual Florida House bill details
        """
        try:
            response = self.session.get(bill_url, timeout=15)

            # Check if we got the rejection message
            if "requested URL was rejected" in response.text.lower():
                print(f"❌ URL rejected by server: {bill_url}")
                return None

            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract bill number from URL
            bill_match = re.search(r'BillId=(\d+)', bill_url)
            if not bill_match:
                return None

            bill_num = bill_match.group(1)
            page_text = soup.get_text().lower()

            # **FILTER: Only return bills that are NEW and haven't been voted on**
            # Check for final/completion status - SKIP these bills
            final_completion_patterns = [
                r'bill\s+(passed|failed|died|killed|defeated)',
                r'(signed into law|became law|enacted)',
                r'(vetoed|withdrawn)\s+(by|from)',
                r'final\s+(passage|vote|reading)\s+(passed|failed)',
                r'governor\s+(signed|vetoed)',
                r'(cs\s+passed|committee\s+substitute\s+passed)',
                r'status:\s*(passed|failed|died|enacted|signed|vetoed|withdrawn)'
            ]

            bill_is_completed = False
            completion_reason = None
            bill_status = "Active"

            for pattern in final_completion_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    bill_is_completed = True
                    completion_reason = match.group(0).lower()

                    # Determine the specific status
                    if any(word in completion_reason for word in ['passed', 'enacted', 'signed into law', 'became law']):
                        bill_status = "Passed"
                    elif any(word in completion_reason for word in ['failed', 'died', 'killed', 'defeated']):
                        bill_status = "Failed"
                    elif 'vetoed' in completion_reason:
                        bill_status = "Vetoed"
                    elif 'withdrawn' in completion_reason:
                        bill_status = "Withdrawn"
                    else:
                        bill_status = "Completed"
                    break

            # Only skip if it's clearly an old completed bill (no recent activity)
            if bill_is_completed:
                import datetime
                current_year = datetime.datetime.now().year

                # Check if there's recent activity (current or previous year)
                has_recent_activity = (str(current_year) in page_text or
                                       str(current_year - 1) in page_text or
                                       '2024' in page_text or '2025' in page_text)

                if not has_recent_activity:
                    print(
                        f"⏭️ Skipping old completed bill {bill_num} (reason: {completion_reason}, no recent activity)")
                    return None
                else:
                    print(
                        f"✅ Including recently completed bill {bill_num} (status: {bill_status}, reason: {completion_reason})")

            # Look for ACTIVE/NEW status indicators - KEEP these bills
            active_status_patterns = [
                r'(filed|introduced|referred)',
                r'in\s+(committee|subcommittee)',
                r'(pending|awaiting|under\s+consideration)',
                r'(first|second|third)\s+reading',
                r'scheduled\s+for',
                r'committee\s+(hearing|meeting)',
                r'(reported|advanced)\s+from',
                r'status:\s*(filed|introduced|referred|pending|active)',
                r'(2024|2025)',  # Recent activity
            ]

            # If not completed, check for active status indicators
            if not bill_is_completed:
                is_active = False

                for pattern in active_status_patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        is_active = True
                        bill_status = match.group(0).strip().title()
                        break

                # If no clear status found, assume it's active if from recent year
                if not is_active:
                    import datetime
                    current_year = datetime.datetime.now().year
                    if str(current_year) in page_text or str(current_year - 1) in page_text:
                        is_active = True
                        bill_status = "Filed"
                    else:
                        print(
                            f"⏭️ Skipping bill {bill_num} (no recent activity found)")
                        return None

                print(
                    f"✅ Including active bill {bill_num} (status: {bill_status})")

            # Extract title first - prioritize H2 which contains the bill number and title
            title_selectors = ['h2', 'h1',
                               '.bill-title', '#bill-title', '.title']
            raw_title = ""
            for selector in title_selectors:
                # Get all elements, not just first
                elements = soup.select(selector)
                for elem in elements:
                    candidate_title = elem.get_text(strip=True)
                    # Check if this element contains a bill number pattern
                    if candidate_title and re.search(r'(HB|SB)\s*\d+', candidate_title, re.IGNORECASE):
                        raw_title = candidate_title
                        break
                if raw_title:  # Break outer loop if we found a title with bill number
                    break

            # If no title with bill number found, fall back to first substantial title
            if not raw_title:
                for selector in title_selectors:
                    title_elem = soup.select_one(selector)
                    if title_elem:
                        raw_title = title_elem.get_text(strip=True)
                        if raw_title and len(raw_title) > 5:
                            break

            if not raw_title:
                raw_title = f"Florida Bill {bill_num}"

            # Extract the REAL bill number from the title (not the URL ID)
            # Look for patterns like "HB 123:", "SB 456:", "CS/HB 789:", etc.
            bill_number_match = re.search(
                r'^((?:CS/)*(?:HB|SB)\s*\d+)', raw_title, re.IGNORECASE)

            if bill_number_match:
                # Found real bill number in title
                real_bill_number = bill_number_match.group(1).strip()
                # Standardize format: "HB 123" or "SB 456"
                real_bill_number = re.sub(
                    r'\s+', ' ', real_bill_number.upper())

                # Determine chamber from the real bill number
                if 'HB' in real_bill_number:
                    chamber = "House"
                    sponsor_title = "Rep."
                    bill_type = "House"
                else:
                    chamber = "Senate"
                    sponsor_title = "Sen."
                    bill_type = "Senate"

                # Use real bill number for IDs
                bill_id = real_bill_number  # e.g., "HB 123"
                bill_number = real_bill_number.replace(
                    ' ', '-')  # e.g., "HB-123"

                print(
                    f"📋 Extracted real bill number: {real_bill_number} from title")
            else:
                # Fallback to URL ID method if we can't find real bill number
                print(
                    f"⚠️ Could not extract bill number from title, using URL ID {bill_num}")

                # Determine bill type from page content or URL parameters
                url_lower = bill_url.lower()
                if 'house' in url_lower or 'hb' in page_text or 'house bill' in page_text:
                    bill_id = f"HB {bill_num}"
                    bill_number = f"HB-{bill_num}"
                    chamber = "House"
                    sponsor_title = "Rep."
                    bill_type = "House"
                else:
                    bill_id = f"SB {bill_num}"
                    bill_number = f"SB-{bill_num}"
                    chamber = "Senate"
                    sponsor_title = "Sen."
                    bill_type = "Senate"

            # Clean title by removing bill number from the beginning
            title = re.sub(r'^((?:CS/)*(?:SB|HB)\s*\d+):\s*', '',
                           raw_title, flags=re.IGNORECASE).strip()

            # If title is now empty or too short, use the raw title
            if not title or len(title) < 10:
                title = raw_title

            # Extract sponsor
            sponsor = "Unknown"
            sponsor_patterns = [
                r'sponsor[^:]*:\s*([^<\n]+)',
                r'by\s+([^<\n,;]+)',
                r'introduced\s+by\s+([^<\n,;]+)'
            ]

            page_text = soup.get_text()
            for pattern in sponsor_patterns:
                sponsor_match = re.search(pattern, page_text, re.IGNORECASE)
                if sponsor_match:
                    sponsor_name = sponsor_match.group(1).strip()
                    sponsor = f"{sponsor_title} {sponsor_name}"
                    break

            # Extract summary/description
            summary = ""
            summary_selectors = [
                '.bill-summary', '.summary', '.description',
                '#summary', '#description', '.bill-text',
                'div[class*="summary"]', 'div[class*="description"]'
            ]

            for selector in summary_selectors:
                elem = soup.select_one(selector)
                if elem:
                    text = elem.get_text(strip=True)
                    if len(text) > 50:  # Make sure it's substantial
                        summary = text
                        break

            # If no summary found, try to extract from paragraphs
            if not summary:
                paragraphs = soup.find_all('p')
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if len(text) > 100:  # Look for substantial paragraphs
                        summary = text
                        break

            # If still no summary, use title as summary
            if not summary:
                summary = f"Florida {bill_type} Bill {bill_num}: {title}"

            # Clean up summary
            summary = re.sub(r'\s+', ' ', summary)
            if len(summary) > 500:
                summary = summary[:500] + "..."

            # Use the direct bill URL as the source URL
            source_url = bill_url

            return {
                'title': title,
                'summary': summary,
                'sponsor': sponsor,
                'source_url': source_url,
                'source': 'florida',
                'bill_id': bill_id,
                'bill_number': bill_number,  # Properly formatted number
                'state': 'FL',
                'chamber': chamber,
                'session': '2025',
                'status': bill_status,
                'last_action': bill_status,
                'last_action_date': '',
                'completion_reason': completion_reason if bill_is_completed else None
            }

        except Exception as e:
            print(f"❌ Failed to scrape House bill detail from {bill_url}: {e}")
            return None


def fetch_recent_florida_bills(limit: int = None) -> List[Dict]:
    """
    Fetch ALL active Florida bills using direct web scraping from flhouse.gov
    (This site includes both House and Senate bills)

    Args:
        limit: Ignored - returns all active bills found

    Returns:
        List of all active Florida bills (typically 30-40 bills)
    """
    print("🌴 Fetching Florida bills via flhouse.gov scraping...")

    try:
        scraper = FloridaBillScraper()

        # Get ALL Florida bills from the house site (includes both House and Senate)
        # Process all bills to find the best active ones
        all_bills = scraper.scrape_florida_bills_from_house_site(
            limit=999)  # Get all active bills

        # Ensure all bills have the correct source
        for bill in all_bills:
            bill['source'] = 'florida'

        # Remove duplicates by bill_id (some bills appear multiple times)
        seen_bills = {}
        unique_bills = []
        for bill in all_bills:
            bill_id = bill.get('bill_id', '')
            if bill_id not in seen_bills:
                seen_bills[bill_id] = True
                unique_bills.append(bill)

        print(
            f"🔍 Removed duplicates: {len(all_bills)} -> {len(unique_bills)} unique bills")

        # Sort bills by bill number (newest first) and return the requested limit
        # Assuming higher bill numbers are more recent
        try:
            sorted_bills = sorted(unique_bills, key=lambda x: int(
                x.get('bill_id', '').split()[-1]), reverse=True)
        except:
            sorted_bills = unique_bills  # Fallback if sorting fails

        # Return ALL active bills (sorted by bill number, newest first)
        all_active_bills = sorted_bills

        print(
            f"✅ Successfully processed all bills, found {len(unique_bills)} unique active bills total")
        print(
            f"📋 Returning ALL {len(all_active_bills)} active bills (sorted by bill number)")

        print(f"\n📋 Active Florida Bills Found:")
        for i, bill in enumerate(all_active_bills, 1):
            print(
                f"   {i}. {bill.get('bill_number', 'N/A')}: {bill.get('title', 'N/A')[:50]}...")

        return all_active_bills

    except Exception as e:
        print(f"❌ Failed to fetch Florida bills: {e}")
        print("🚫 No fallback data - returning empty list")
        return []
