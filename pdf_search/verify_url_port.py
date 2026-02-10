import requests
import sys

# Test the URL format constructed by config.py
URL_WITH_PORT = "https://endee-1.onrender.com:443"

def check_connection():
    print(f"Testing connection to {URL_WITH_PORT}...")
    try:
        resp = requests.get(f"{URL_WITH_PORT}/api/v1/index/list", timeout=10)
        print(f"Status Code: {resp.status_code}")
        
        if resp.status_code == 200:
            print("SUCCESS: Connection with port 443 works")
            return True
        else:
            print(f"FAILURE: Status {resp.status_code}")
            return False
    except Exception as e:
        print(f"FAILURE: Connection error: {e}")
        return False

if __name__ == "__main__":
    if check_connection():
        sys.exit(0)
    else:
        sys.exit(1)
