#!/usr/bin/env python3
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing analyzer.summary function...")

try:
    from analyzer.summary import summarize_bill
    print("✅ Successfully imported summarize_bill")
except Exception as e:
    print(f"❌ Error importing summarize_bill: {e}")
    sys.exit(1)

# Test the function
try:
    result = summarize_bill(
        title="Test Bill",
        summary="This is a test bill summary",
        sponsor="Test Sponsor"
    )
    print("✅ summarize_bill function executed successfully")
    print(f"Result: {result}")
except Exception as e:
    print(f"❌ Error executing summarize_bill: {e}")
    import traceback
    traceback.print_exc()
