import os
import json
from datetime import datetime


def create_digest(reports, path="data/latest_digest.md"):
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

    # Also create a JSON file for the web interface
    json_data = {
        "generated_at": now,
        "reports": reports
    }

    json_path = path.replace(".md", ".json")
    with open(json_path, "w") as f:
        json.dump(json_data, f, indent=2)

    print(f"Digest saved to {path}")
    print(f"JSON data saved to {json_path}")


def parse_gpt4_analysis(content):
    """
    Parse the structured GPT-4 analysis into components
    """
    sections = {
        'plain_summary': '',
        'who_helps': '',
        'who_hurts': '',
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
        elif '**WHO THIS HELPS:**' in line_upper:
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = 'who_helps'
            current_content = []
        elif '**WHO THIS COULD HURT:**' in line_upper:
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = 'who_hurts'
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
