import os
from openai import OpenAI
from dotenv import load_dotenv
from .cache_manager import get_cache

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client with error handling


def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable is required but not set. Please add it to your environment variables.")
    return OpenAI(api_key=api_key)


def summarize_bill(title, summary, sponsor, bill_id=None, status="active"):
    """
    Generate a structured analysis of a bill using GPT-4.
    Uses caching to avoid re-analyzing the same bills.
    """
    # Get cache instance
    cache = get_cache()

    # Use bill_id if provided, otherwise generate a temporary one
    if bill_id is None:
        bill_id = f"temp_{hash(title + summary) % 10000}"

    # Check if bill is already cached
    if cache.is_bill_cached(bill_id, title, summary):
        cached_result = cache.get_cached_analysis(bill_id, title, summary)
        if cached_result:
            return cached_result.get("analysis", "")

    print(f"🤖 Generating new analysis for {bill_id} (not in cache)")

    try:
        client = get_openai_client()
    except ValueError as e:
        return f"Configuration Error: {str(e)}"

    prompt = f"""
    Analyze this legislation and provide a structured response in the following format:

    **PLAIN ENGLISH SUMMARY:**
    [Write a clear, jargon-free explanation that any citizen can understand]

    **BENEFITS:**
    [List the main advantages and positive outcomes of this legislation]

    **DRAWBACKS:**
    [List the main disadvantages and potential negative consequences]

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

        analysis_result = response.choices[0].message.content

        # Cache the result for future use with status tracking
        cache.cache_bill_analysis(
            bill_id, title, summary, analysis_result, status)

        return analysis_result

    except Exception as e:
        return f"Analysis Error: Unable to generate analysis. {str(e)}"


def get_detailed_analysis(bill_title, bill_summary, question, bill_id=None):
    """
    Answer specific questions about a bill using GPT-4.
    Uses caching for frequently asked questions.
    """
    # Get cache instance
    cache = get_cache()

    # Create a unique key for this specific question
    question_key = f"{bill_id or 'temp'}_{hash(question) % 10000}"

    # Check if this specific question about this bill is cached
    if cache.is_bill_cached(question_key, bill_title, f"{bill_summary}|Q:{question}"):
        cached_result = cache.get_cached_analysis(
            question_key, bill_title, f"{bill_summary}|Q:{question}")
        if cached_result:
            return cached_result.get("analysis", "")

    print(
        f"🤖 Generating detailed analysis for question about {bill_id or 'bill'}")

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

        analysis_result = response.choices[0].message.content

        # Cache the result for future use with status tracking
        cache.cache_bill_analysis(question_key, bill_title, f"{bill_summary}|Q:{question}",
                                  analysis_result, "active")

        return analysis_result

    except Exception as e:
        return f"Error: Unable to generate response. {str(e)}"
