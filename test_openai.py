#!/usr/bin/env python3
import os
from openai import OpenAI

# Test script to verify OpenAI API is working correctly


def test_openai():
    print("Testing OpenAI API...")

    # Check if API key is set
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable not set")
        return False

    print(f"✅ API key is set")

    # Create client
    try:
        client = OpenAI(api_key=api_key)
        print("✅ OpenAI client created successfully")
    except Exception as e:
        print(f"❌ Error creating OpenAI client: {e}")
        return False

    # Test API call
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Use cheaper model for testing
            messages=[
                {"role": "user", "content": "Say hello"}
            ],
            max_tokens=10
        )
        print("✅ OpenAI API call successful")
        print(f"Response: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"❌ OpenAI API call failed: {e}")
        return False


if __name__ == "__main__":
    test_openai()
