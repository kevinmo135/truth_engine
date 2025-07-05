import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client with error handling


def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable is required but not set. Please add it to your environment variables.")
    return OpenAI(api_key=api_key)


def summarize_bill(title, summary, sponsor):
    """
    Generate a structured analysis of a bill using GPT-4.
    """
    try:
        client = get_openai_client()
    except ValueError as e:
        return f"Configuration Error: {str(e)}"

    prompt = f"""
    Analyze this legislation and provide a structured response in the following format:

    **PLAIN ENGLISH SUMMARY:**
    [Write a clear, jargon-free explanation that any citizen can understand]

    **WHO THIS HELPS:**
    [List specific groups, demographics, or stakeholders who would benefit]

    **WHO THIS COULD HURT:**
    [List potential negative impacts on specific groups or interests]

    **SHORT-TERM IMPACT (1-2 years):**
    [Immediate effects if this becomes law]

    **LONG-TERM IMPACT (5+ years):**
    [Long-range consequences and implications]

    **KEY CONTROVERSIES:**
    [Main points of debate and opposition arguments]

    **COST/SAVINGS:**
    [Financial impact - spending, savings, or revenue effects]

    BILL DETAILS:
    Title: {title}
    Sponsor: {sponsor}
    Summary: {summary}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a nonpartisan policy analyst who explains legislation clearly and objectively to help citizens understand government actions."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.7
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Analysis Error: Unable to generate analysis. {str(e)}"


def get_detailed_analysis(bill_title, bill_summary, question):
    """
    Answer specific questions about a bill using GPT-4.
    """
    try:
        client = get_openai_client()
    except ValueError as e:
        return f"Configuration Error: {str(e)}"

    prompt = f"""
    You are answering questions about this legislation:

    Bill: {bill_title}
    Summary: {bill_summary}

    User Question: {question}

    Provide a detailed, factual answer based on the bill information. Be specific and cite relevant aspects of the legislation.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful policy analyst who answers questions about legislation clearly and accurately."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.7
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Error: Unable to generate response. {str(e)}"
