import json
import os
from datetime import datetime
from typing import Dict, Optional
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


# Global cache instance
_cache_instance = None


def get_cache() -> BillAnalysisCache:
    """Get the global cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = BillAnalysisCache()
    return _cache_instance
