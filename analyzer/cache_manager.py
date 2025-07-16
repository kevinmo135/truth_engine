import json
import os
from datetime import datetime
from typing import Dict, Optional, List
import hashlib


class BillAnalysisCache:
    """
    Manages caching of bill analyses to avoid re-processing with OpenAI
    """

    def __init__(self, cache_file: str = "data/processed_bills.json"):
        self.cache_file = cache_file
        self.cache_data = {}
        self._load_cache()

    def _load_cache(self):
        """Load existing cache from file"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache_data = json.load(f)
                print(
                    f"📄 Loaded cache with {len(self.cache_data)} processed bills")
            else:
                print("📄 No existing cache file found, starting fresh")
                self.cache_data = {}
        except Exception as e:
            print(f"⚠️ Error loading cache: {e}")
            self.cache_data = {}

    def _save_cache(self):
        """Save cache to file"""
        try:
            # Ensure data directory exists
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)

            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_data, f, indent=2, ensure_ascii=False)
            print(f"💾 Cache saved with {len(self.cache_data)} processed bills")
        except Exception as e:
            print(f"⚠️ Error saving cache: {e}")

    def _generate_bill_key(self, bill_id: str, title: str, summary: str) -> str:
        """
        Generate a unique key for a bill based on its content
        This helps identify bills even if bill_id changes slightly
        """
        # Create a hash of the bill content for uniqueness
        # First 200 chars of summary
        content = f"{bill_id}|{title}|{summary[:200]}"
        return hashlib.md5(content.encode()).hexdigest()

    def is_bill_cached(self, bill_id: str, title: str, summary: str) -> bool:
        """Check if a bill has already been processed"""
        bill_key = self._generate_bill_key(bill_id, title, summary)
        return bill_key in self.cache_data

    def get_cached_analysis(self, bill_id: str, title: str, summary: str) -> Optional[Dict]:
        """Retrieve cached analysis for a bill"""
        bill_key = self._generate_bill_key(bill_id, title, summary)

        if bill_key in self.cache_data:
            cached_data = self.cache_data[bill_key]
            # Increment access count for cache hit tracking
            cached_data["access_count"] = cached_data.get(
                "access_count", 1) + 1
            self.cache_data[bill_key] = cached_data
            # Save cache to persist the updated access count
            self._save_cache()
            print(
                f"💡 Using cached analysis for {bill_id} (cached on {cached_data.get('cached_date', 'unknown')})")
            return cached_data

        return None

    def cache_analysis(self, bill_id: str, title: str, summary: str, sponsor: str, analysis: str):
        """Store analysis in cache"""
        bill_key = self._generate_bill_key(bill_id, title, summary)

        cache_entry = {
            "bill_id": bill_id,
            "title": title,
            "summary": summary,
            "sponsor": sponsor,
            "analysis": analysis,
            "cached_date": datetime.now().isoformat(),
            "access_count": 1
        }

        # If already exists, increment access count
        if bill_key in self.cache_data:
            cache_entry["access_count"] = self.cache_data[bill_key].get(
                "access_count", 0) + 1

        self.cache_data[bill_key] = cache_entry
        self._save_cache()

        print(f"💾 Cached analysis for {bill_id}")

    def get_cache_stats(self) -> Dict:
        """Get statistics about the cache"""
        total_bills = len(self.cache_data)
        total_access = sum(entry.get("access_count", 1)
                           for entry in self.cache_data.values())
        # Calculate calls saved: every access beyond the first one is a saved call
        calls_saved = sum(max(0, entry.get("access_count", 1) - 1)
                          for entry in self.cache_data.values())

        return {
            "total_cached_bills": total_bills,
            "total_cache_hits": total_access,
            "estimated_openai_calls_saved": calls_saved
        }

    def clear_cache(self):
        """Clear all cached data"""
        self.cache_data = {}
        self._save_cache()
        print("🗑️ Cache cleared")

    def clear_stats(self):
        """Clear cache statistics (reset access counts) while keeping cached analyses"""
        for bill_key, entry in self.cache_data.items():
            # Reset access count to 1 (representing just the initial processing)
            entry["access_count"] = 1

        self._save_cache()
        print("📊 Cache statistics cleared (access counts reset)")

    def cache_bill_analysis(self, bill_id: str, title: str, summary: str,
                            analysis: str, status: str = "active",
                            status_date: str = None) -> bool:
        """Cache a bill analysis with status tracking"""
        from datetime import datetime

        bill_key = self._generate_bill_key(bill_id, title, summary)

        # Get existing entry or create new one
        existing_entry = self.cache_data.get(bill_key, {})

        # Track status changes
        current_status = existing_entry.get('status', 'active')
        current_date = datetime.now().isoformat()

        # If status changed, update the status change date
        if status != current_status:
            status_change_date = current_date
            print(
                f"📈 Bill {bill_id} status changed: {current_status} -> {status}")
        else:
            status_change_date = existing_entry.get(
                'status_change_date', current_date)

        self.cache_data[bill_key] = {
            'bill_id': bill_id,
            'title': title,
            'summary': summary,
            'analysis': analysis,
            'cached_date': existing_entry.get('cached_date', current_date),
            'last_accessed': current_date,
            'access_count': existing_entry.get('access_count', 0) + 1,
            'status': status,
            'status_change_date': status_change_date,
            'original_status': existing_entry.get('original_status', 'active')
        }

        return self._save_cache()

    def get_bills_by_status(self) -> Dict[str, List[Dict]]:
        """Get bills grouped by their current status"""
        from datetime import datetime, timedelta

        status_groups = {
            'active': [],
            'passed': [],
            'failed': [],
            'vetoed': [],
            'withdrawn': []
        }

        current_date = datetime.now()
        one_month_ago = current_date - timedelta(days=30)

        for bill_key, bill_data in self.cache_data.items():
            status = bill_data.get('status', 'active').lower()

            # Check if bill should be cleaned up (older than 1 month and not active)
            status_change_date = bill_data.get('status_change_date')
            if status_change_date and status != 'active':
                try:
                    change_date = datetime.fromisoformat(
                        status_change_date.replace('Z', '+00:00'))
                    if change_date < one_month_ago:
                        # Mark for cleanup but don't remove during iteration
                        continue
                except:
                    pass

            # Group by status
            if status == 'active':
                status_groups['active'].append(bill_data)
            elif status in ['passed', 'enacted', 'signed']:
                status_groups['passed'].append(bill_data)
            elif status in ['failed', 'died', 'killed', 'defeated']:
                status_groups['failed'].append(bill_data)
            elif status in ['vetoed']:
                status_groups['vetoed'].append(bill_data)
            elif status in ['withdrawn']:
                status_groups['withdrawn'].append(bill_data)

        return status_groups

    def cleanup_old_bills(self) -> int:
        """Remove bills older than 1 month that are not active"""
        from datetime import datetime, timedelta

        current_date = datetime.now()
        one_month_ago = current_date - timedelta(days=30)

        bills_to_remove = []

        for bill_key, bill_data in self.cache_data.items():
            status = bill_data.get('status', 'active').lower()
            status_change_date = bill_data.get('status_change_date')

            # Only cleanup non-active bills
            if status != 'active' and status_change_date:
                try:
                    change_date = datetime.fromisoformat(
                        status_change_date.replace('Z', '+00:00'))
                    if change_date < one_month_ago:
                        bills_to_remove.append(bill_key)
                except:
                    pass

        # Remove old bills
        for bill_key in bills_to_remove:
            bill_id = self.cache_data[bill_key].get('bill_id', 'unknown')
            print(f"🗑️ Cleaning up old bill: {bill_id}")
            del self.cache_data[bill_key]

        if bills_to_remove:
            self._save_cache()
            print(f"✅ Cleaned up {len(bills_to_remove)} old bills")

        return len(bills_to_remove)


# Global cache instance
_cache_instance = None


def get_cache() -> BillAnalysisCache:
    """Get the global cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = BillAnalysisCache()
    return _cache_instance
