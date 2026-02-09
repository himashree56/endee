import requests
import json

try:
    print("Sending request to http://localhost:8001/api/chat...")
    resp = requests.post("http://localhost:8001/api/chat", json={"question": "hi", "history": []})
    print(f"Status: {resp.status_code}")
    try:
        data = resp.json()
        if "detail" in data:
            print("Full Error Detail:")
            print(data["detail"])
        else:
            print("Response Data:")
            print(json.dumps(data, indent=2))
    except:
        print("Raw Response:")
        print(resp.text)

except Exception as e:
    print(f"Request failed: {e}")
