import requests
import json
import time

BASE_URL = "http://localhost:8000"
FILENAME = "Machine-learning- Stephen Marshland.pdf"

def test_summarize():
    print(f"Requesting summary for {FILENAME}...")
    start = time.time()
    try:
        response = requests.post(
            f"{BASE_URL}/api/summarize", 
            json={"filename": FILENAME, "length": "short"},
            timeout=120
        )
        duration = time.time() - start
        
        print(f"Status: {response.status_code} (took {duration:.1f}s)")
        
        if response.status_code == 200:
            data = response.json()
            summary = data.get("summary")
            print(f"Summary length: {len(summary) if summary else 0} chars")
            print(f"Summary content:\n{summary[:200]}..." if summary else "Summary is missing/empty")
            
            if summary and "Error" not in summary:
                print("✓ Summarization passed!")
            else:
                print("❌ Summarization returned error message.")
        else:
            print(f"❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_summarize()
