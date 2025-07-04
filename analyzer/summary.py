import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def summarize_bill(title, summary, sponsor):
    prompt = f"""
You are an expert civic policy analyst. Analyze the following legislation with depth and nuance. Provide clear, accessible insights that help citizens understand the real-world implications.

Bill Title: {title}
Summary: {summary}
Sponsor: {sponsor}

Please provide a comprehensive analysis in the following format:

**Plain English Summary:**
[2-3 sentences explaining what this bill actually does in simple terms]

**Who This Helps:**
[Specific groups, communities, or industries that would benefit]

**Who This Could Hurt:**
[Specific groups that might face negative impacts or increased costs]

**Short-Term Impact (1-2 years):**
[Immediate effects if this bill passes]

**Long-Term Impact (5+ years):**
[Broader societal and economic implications]

**Key Controversies:**
[Main points of debate or opposition this bill might face]

**Estimated Cost/Savings:**
[If mentioned in summary, or note if unclear]
"""

    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            messages=[
                {"role": "system", "content": "You are an expert policy analyst who explains complex legislation in clear, accessible language. Focus on real-world impacts and be objective about both benefits and drawbacks."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ OpenAI API error: {e}")
        return "Error: Unable to generate summary"


def get_detailed_analysis(title, summary, sponsor, user_question=""):
    """
    Generate a detailed, interactive analysis for the web interface
    """
    base_prompt = f"""
Bill Title: {title}
Summary: {summary}
Sponsor: {sponsor}
"""

    if user_question:
        prompt = f"""
{base_prompt}

User Question: {user_question}

As an expert policy analyst, answer the user's specific question about this bill. Provide detailed, factual information while maintaining objectivity. Include relevant context and implications.
"""
    else:
        prompt = f"""
{base_prompt}

Provide a comprehensive analysis of this legislation including:
- Detailed explanation of mechanisms and implementation
- Stakeholder analysis (winners/losers)
- Economic implications and budget impact
- Timeline for implementation
- Potential legal challenges
- Comparison to similar past legislation
- Public opinion considerations

Be thorough but accessible to educated citizens.
"""

    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            messages=[
                {"role": "system", "content": "You are a senior policy analyst providing detailed, nuanced analysis of legislation. Be comprehensive, objective, and educational."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating detailed analysis: {e}"
