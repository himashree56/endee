import requests
import sys

URL = "https://endee-1.onrender.com"

def check_connection():
    print(f"Testing connection to {URL}...")
    try:
        # Try health/list endpoint
        # EndeeClient uses /api/v1/index/list
        resp = requests.get(f"{URL}/api/v1/index/list", timeout=10)
        print(f"Status Code: {resp.status_code}")
        print(f"Response: {resp.text[:500]}")
        
        if resp.status_code == 200:
            print("SUCCESS: Connected to Endee Server")
            return True
        else:
            print("FAILURE: Remote server returned error")
            return False
    except Exception as e:
        print(f"FAILURE: Connection error: {e}")
        return False

if __name__ == "__main__":
    if check_connection():
        sys.exit(0)
    else:
        sys.exit(1)
