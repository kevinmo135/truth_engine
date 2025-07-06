import os
import json
from datetime import datetime


def create_digest(reports, path="data/latest_digest.md"):
    from analyzer.cache_manager import get_cache

    # Get cache instance for status grouping and cleanup
    cache = get_cache()

    # Clean up old bills (older than 1 month)
    cleaned_count = cache.cleanup_old_bills()
    if cleaned_count > 0:
        print(f"🗑️ Cleaned up {cleaned_count} old bills from cache")

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    content = f"# Daily Truth Digest\nGenerated: {now}\n\n"

    content += "## Most Impactful Decisions\n"
    for i, report in enumerate(reports[:3]):
        summary = report.get('parsed', {}).get('plain_summary', '') or report.get(
            'original_summary', '')[:200] + '...'
        content += f"**{i+1}. {report['title']}**\n{summary}\n\n"

    content += "## Full Breakdown\n"
    for report in reports:
        content += f"### {report['title']}\n"
        content += f"**Sponsor:** {report['sponsor']}\n\n"
        content += f"{report['analysis']}\n\n"
        content += "---\n\n"

    with open(path, "w") as f:
        f.write(content)

    # Get bills grouped by status for web interface
    status_groups = cache.get_bills_by_status()

    # Also create a JSON file for the web interface with status grouping
    json_data = {
        "generated_at": now,
        "reports": reports,
        "status_groups": status_groups,
        "summary_stats": {
            "total_bills": len(reports),
            "active_bills": len(status_groups.get('active', [])),
            "passed_bills": len(status_groups.get('passed', [])),
            "failed_bills": len(status_groups.get('failed', [])),
            "vetoed_bills": len(status_groups.get('vetoed', [])),
            "withdrawn_bills": len(status_groups.get('withdrawn', [])),
            "cleaned_up_bills": cleaned_count
        }
    }

    json_path = path.replace(".md", ".json")
    with open(json_path, "w") as f:
        json.dump(json_data, f, indent=2)

    print(f"Digest saved to {path}")
    print(f"JSON data saved to {json_path}")
    print(
        f"📊 Status summary: {json_data['summary_stats']['active_bills']} active, {json_data['summary_stats']['passed_bills']} passed, {json_data['summary_stats']['failed_bills']} failed")


def parse_gpt4_analysis(content):
    """
    Parse the structured GPT-4 analysis into components
    """
    sections = {
        'plain_summary': '',
        'benefits': '',
        'drawbacks': '',
        'short_term': '',
        'long_term': '',
        'controversies': '',
        'cost_savings': ''
    }

    lines = content.split('\n')
    current_section = None
    current_content = []

    for line in lines:
        line = line.strip()
        line_upper = line.upper()
        if '**PLAIN ENGLISH SUMMARY:**' in line_upper:
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = 'plain_summary'
            current_content = []
        elif '**BENEFITS:**' in line_upper:
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = 'benefits'
            current_content = []
        elif '**DRAWBACKS:**' in line_upper:
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = 'drawbacks'
            current_content = []
        elif '**SHORT-TERM IMPACT' in line_upper:
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = 'short_term'
            current_content = []
        elif '**LONG-TERM IMPACT' in line_upper:
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = 'long_term'
            current_content = []
        elif '**KEY CONTROVERSIES:**' in line_upper:
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = 'controversies'
            current_content = []
        elif '**COST/SAVINGS:**' in line_upper or '**ESTIMATED COST/SAVINGS:**' in line_upper:
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = 'cost_savings'
            current_content = []
        elif current_section and line:
            current_content.append(line)

    # Don't forget the last section
    if current_section:
        sections[current_section] = '\n'.join(current_content).strip()

    return sections
