
import requests
import time
import sys
from pathlib import Path

BASE_URL = "http://localhost:8000"
PDF_PATH = Path("pdfs/test_doc.pdf")

def test_workflow():
    print(f"Checking health at {BASE_URL}/api/health ...")
    try:
        r = requests.get(f"{BASE_URL}/api/health", timeout=5)
        print(f"Health: {r.status_code} {r.json()}")
    except Exception as e:
        print(f"Server not up: {e}")
        return

    print(f"Uploading {PDF_PATH}...")
    with open(PDF_PATH, "rb") as f:
        files = {"files": (PDF_PATH.name, f, "application/pdf")}
        r = requests.post(f"{BASE_URL}/api/upload", files=files)
        print(f"Upload Status: {r.status_code}")
        print(f"Upload Response: {r.json()}")

    print("Waiting for background ingestion (10s)...")
    time.sleep(10)

    print("Fetching documents...")
    r = requests.get(f"{BASE_URL}/api/documents")
    print(f"Documents Status: {r.status_code}")
    doc_resp = r.json()
    print(f"Documents Response: {doc_resp}")
    
    docs = doc_resp.get("documents", [])
    if any(d["filename"] == PDF_PATH.name for d in docs):
        print("SUCCESS: Document found in list.")
    else:
        print("FAILURE: Document NOT found in list.")

if __name__ == "__main__":
    test_workflow()
