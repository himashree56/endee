import requests
import json

try:
    print("Testing /api/search...")
    response = requests.post(
        "http://localhost:8000/api/search",
        json={"query": "agentic ai", "top_k": 3}
    )
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Success!")
        print(json.dumps(response.json(), indent=2)[:500] + "...")
    else:
        print("Failed!")
        print(response.text)
except Exception as e:
    print(f"Error: {e}")
