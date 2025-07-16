import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import os


class LegislativeAnalytics:
    """Analyzes legislative data for trends, patterns, and predictions"""

    def __init__(self):
        self.party_success_rates = {
            'republican': 0.12,  # Historical average
            'democrat': 0.15,
            'independent': 0.08
        }

        self.chamber_success_rates = {
            'house': 0.10,
            'senate': 0.18
        }

        # Common legislative keywords for topic analysis
        self.topic_keywords = {
            'Healthcare': ['health', 'medical', 'medicare', 'medicaid', 'insurance', 'hospital', 'patient', 'care'],
            'Immigration': ['immigration', 'border', 'visa', 'refugee', 'asylum', 'citizenship', 'alien'],
            'Economy': ['economy', 'economic', 'jobs', 'employment', 'business', 'trade', 'tax', 'budget'],
            'Education': ['education', 'school', 'student', 'teacher', 'university', 'college', 'learning'],
            'Environment': ['environment', 'climate', 'clean', 'energy', 'carbon', 'pollution', 'conservation'],
            'Defense': ['defense', 'military', 'army', 'navy', 'security', 'veteran', 'armed forces'],
            'Infrastructure': ['infrastructure', 'roads', 'bridges', 'transportation', 'highway', 'transit'],
            'Technology': ['technology', 'cyber', 'internet', 'digital', 'data', 'privacy', 'artificial intelligence'],
            'Criminal Justice': ['criminal', 'justice', 'crime', 'police', 'prison', 'court', 'law enforcement'],
            'Social Issues': ['social', 'rights', 'discrimination', 'equality', 'civil', 'housing', 'welfare']
        }

    def analyze_trending_topics(self, bills: List[Dict]) -> List[Dict]:
        """Analyze which topics are trending in current legislation"""
        topic_counts = Counter()
        topic_bills = defaultdict(list)

        for bill in bills:
            text = f"{bill.get('title', '')} {bill.get('summary', '')}".lower()

            for topic, keywords in self.topic_keywords.items():
                if any(keyword in text for keyword in keywords):
                    topic_counts[topic] += 1
                    topic_bills[topic].append(bill)

        # Calculate trend data
        trending_topics = []
        total_bills = len(bills)

        for topic, count in topic_counts.most_common(10):
            percentage = (count / total_bills) * 100 if total_bills > 0 else 0

            # Calculate "heat" score based on recency and frequency
            recent_bills = [b for b in topic_bills[topic]
                            if self._is_recent_bill(b)]
            heat_score = min(100, (len(recent_bills) / max(1, count)) * 100)

            trending_topics.append({
                'topic': topic,
                'count': count,
                'percentage': round(percentage, 1),
                'heat_score': round(heat_score, 1),
                'recent_count': len(recent_bills),
                # Top 3 bills for preview
                'sample_bills': topic_bills[topic][:3]
            })

        return trending_topics

    def predict_success_probability(self, bill: Dict) -> Dict:
        """Predict the likelihood of a bill passing based on various factors"""
        base_probability = 0.10  # Base 10% success rate

        # Factor adjustments
        probability_factors = {
            'chamber_bonus': 0,
            'sponsor_bonus': 0,
            'bipartisan_bonus': 0,
            'topic_bonus': 0,
            'length_penalty': 0
        }

        # Chamber factor
        chamber = bill.get('chamber', '').lower()
        if chamber in self.chamber_success_rates:
            chamber_bonus = self.chamber_success_rates[chamber] - 0.10
            probability_factors['chamber_bonus'] = chamber_bonus

        # Sponsor party (simplified - would need real data)
        sponsor = bill.get('sponsor', '').lower()
        if 'democrat' in sponsor or 'republican' in sponsor:
            probability_factors['sponsor_bonus'] = 0.02

        # Bipartisan indicators
        text = f"{bill.get('title', '')} {bill.get('summary', '')}".lower()
        bipartisan_keywords = [
            'bipartisan', 'across the aisle', 'republican and democrat', 'both parties']
        if any(keyword in text for keyword in bipartisan_keywords):
            probability_factors['bipartisan_bonus'] = 0.15

        # Topic popularity (trending topics have higher success rates)
        topic_found = False
        for topic, keywords in self.topic_keywords.items():
            if any(keyword in text for keyword in keywords):
                # Healthcare and Economy bills historically have higher success rates
                if topic in ['Healthcare', 'Economy', 'Defense']:
                    probability_factors['topic_bonus'] = 0.05
                topic_found = True
                break

        # Bill complexity penalty (longer bills are harder to pass)
        summary_length = len(bill.get('summary', ''))
        if summary_length > 1000:
            probability_factors['length_penalty'] = -0.03

        # Calculate final probability
        final_probability = base_probability + \
            sum(probability_factors.values())
        final_probability = max(
            0.01, min(0.95, final_probability))  # Cap between 1% and 95%

        return {
            'probability': round(final_probability * 100, 1),
            'confidence': self._calculate_confidence(probability_factors),
            'factors': probability_factors,
            'risk_level': self._get_risk_level(final_probability)
        }

    def generate_timeline_insights(self, bills: List[Dict]) -> Dict:
        """Generate insights about bill timelines and legislative patterns"""

        # Status distribution
        status_counts = Counter()
        for bill in bills:
            status = bill.get('status', 'unknown').lower()
            status_counts[status] += 1

        # Chamber distribution
        chamber_counts = Counter()
        for bill in bills:
            chamber = bill.get('chamber', 'unknown').lower()
            chamber_counts[chamber] += 1

        # Source distribution
        source_counts = Counter()
        for bill in bills:
            source = bill.get('source', 'unknown').lower()
            source_counts[source] += 1

        # Average success rate by chamber
        chamber_success = {}
        for chamber in ['house', 'senate']:
            chamber_bills = [b for b in bills if b.get(
                'chamber', '').lower() == chamber]
            if chamber_bills:
                passed_bills = [b for b in chamber_bills if b.get(
                    'status', '').lower() == 'passed']
                success_rate = len(passed_bills) / len(chamber_bills) * 100
                chamber_success[chamber] = round(success_rate, 1)

        return {
            'status_distribution': dict(status_counts),
            'chamber_distribution': dict(chamber_counts),
            'source_distribution': dict(source_counts),
            'chamber_success_rates': chamber_success,
            'total_bills': len(bills),
            'active_bills': sum(1 for b in bills if b.get('status', '').lower() == 'active'),
            'passed_bills': sum(1 for b in bills if b.get('status', '').lower() == 'passed')
        }

    def get_sponsor_insights(self, bills: List[Dict]) -> List[Dict]:
        """Analyze sponsor patterns and productivity"""
        sponsor_stats = defaultdict(
            lambda: {'bills': 0, 'topics': set(), 'success_rate': 0})

        for bill in bills:
            sponsor = bill.get('sponsor', 'Unknown').strip()
            if sponsor and sponsor != 'Unknown':
                sponsor_stats[sponsor]['bills'] += 1

                # Track topics
                text = f"{bill.get('title', '')} {bill.get('summary', '')}".lower(
                )
                for topic, keywords in self.topic_keywords.items():
                    if any(keyword in text for keyword in keywords):
                        sponsor_stats[sponsor]['topics'].add(topic)
                        break

                # Track success (simplified)
                if bill.get('status', '').lower() == 'passed':
                    sponsor_stats[sponsor]['success_rate'] += 1

        # Calculate final stats
        sponsor_insights = []
        for sponsor, stats in sponsor_stats.items():
            if stats['bills'] >= 2:  # Only include sponsors with multiple bills
                success_rate = (
                    stats['success_rate'] / stats['bills']) * 100 if stats['bills'] > 0 else 0

                sponsor_insights.append({
                    'sponsor': sponsor,
                    'bill_count': stats['bills'],
                    'success_rate': round(success_rate, 1),
                    'topic_diversity': len(stats['topics']),
                    'primary_topics': list(stats['topics'])[:3]
                })

        # Sort by bill count
        sponsor_insights.sort(key=lambda x: x['bill_count'], reverse=True)
        return sponsor_insights[:10]  # Top 10 most active sponsors

    def _is_recent_bill(self, bill: Dict) -> bool:
        """Check if a bill is recent (within last 30 days)"""
        # Simplified - in real implementation, would parse actual dates
        return True  # For now, consider all bills recent

    def _calculate_confidence(self, factors: Dict) -> str:
        """Calculate confidence level based on available factors"""
        factor_count = sum(1 for v in factors.values() if v != 0)
        if factor_count >= 3:
            return "High"
        elif factor_count >= 2:
            return "Medium"
        else:
            return "Low"

    def _get_risk_level(self, probability: float) -> str:
        """Get risk level based on success probability"""
        if probability >= 0.30:
            return "High Chance"
        elif probability >= 0.15:
            return "Moderate Chance"
        elif probability >= 0.08:
            return "Low Chance"
        else:
            return "Very Low Chance"


def generate_analytics_report(bills: List[Dict]) -> Dict:
    """Generate comprehensive analytics report"""
    analyzer = LegislativeAnalytics()

    report = {
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_bills_analyzed': len(bills),
        'trending_topics': analyzer.analyze_trending_topics(bills),
        'timeline_insights': analyzer.generate_timeline_insights(bills),
        'sponsor_insights': analyzer.get_sponsor_insights(bills),
        'success_predictions': []
    }

    # Add success predictions for sample bills
    for bill in bills[:20]:  # Top 20 bills
        prediction = analyzer.predict_success_probability(bill)
        report['success_predictions'].append({
            'bill_id': bill.get('bill_id'),
            'title': bill.get('title'),
            'prediction': prediction
        })

    return report


if __name__ == "__main__":
    print("Analytics module - use generate_analytics_report() function")
