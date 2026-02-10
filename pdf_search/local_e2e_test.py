import requests
import json
import time
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
TEST_PDF_NAME = "Machine-learning- Stephen Marshland.pdf"

def print_section(name):
    print(f"\n{'='*40}")
    print(f"TESTING: {name}")
    print(f"{'='*40}")

def test_health():
    print_section("Health Check")
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✓ Health Check Passed")
            return True
        return False
    except Exception as e:
        print(f"❌ Health Check Failed: {e}")
        return False

def wait_for_indexing(filename, timeout=300):
    print(f"Waiting for {filename} to be indexed (Timeout: {timeout}s)...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{BASE_URL}/api/documents", timeout=10)
            if response.status_code == 200:
                data = response.json()
                docs = data.get("documents", [])
                for d in docs:
                    if d['filename'] == filename:
                        if d['chunks'] > 0:
                            print(f"✓ Indexing complete! ({d['chunks']} chunks)")
                            return True
                        else:
                            print(f" - Found file but 0 chunks... indexing in progress?")
            else:
                print(f"Api/documents returned {response.status_code}")
        except Exception as e:
            print(f"Error checking status: {e}")
        
        time.sleep(5)
    
    print("❌ Timeout waiting for indexing.")
    return False

def test_upload(file_path):
    print_section(f"Upload PDF: {file_path}")
    try:
        if not Path(file_path).exists():
            print(f"❌ File not found: {file_path}")
            return False

        with open(file_path, "rb") as f:
            files = {"files": (Path(file_path).name, f, "application/pdf")}
            response = requests.post(f"{BASE_URL}/api/upload", files=files, timeout=300)
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
            print("✓ Upload Accepted")
            # Wait for indexing
            return wait_for_indexing(Path(file_path).name)
        else:
            print(f"❌ Upload Failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Upload Error: {e}")
        return False

def test_search(query="machine learning"):
    print_section(f"Search (Query: '{query}')")
    try:
        payload = {"query": query, "top_k": 3}
        response = requests.post(f"{BASE_URL}/api/search", json=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"Found {len(results)} results.")
            for res in results:
                print(f" - [{res['score']:.4f}] {res['text'][:60]}...")
            if len(results) > 0:
                print("✓ Search Passed")
                return True
            else:
                print("⚠ Search returned 0 results")
                return False
        else:
            print(f"❌ Failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

def test_chat(question, history=[]):
    print_section(f"Chat (Question: '{question}')")
    try:
        payload = {"question": question, "history": history}
        response = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=120)
        if response.status_code == 200:
            data = response.json()
            answer = data.get('answer') or ""
            print("Answer:", answer[:100] + "...")
            print(f"Sources: {len(data.get('sources', []))}")
            print("✓ Chat Passed")
            return True
        else:
            print(f"❌ Failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

def test_adaptive_rag(question):
    print_section(f"Adaptive RAG (Question: '{question}')")
    try:
        payload = {"question": question, "mode": "standard"}
        response = requests.post(f"{BASE_URL}/api/adaptive-rag", json=payload, timeout=120)
        if response.status_code == 200:
            data = response.json()
            answer = data.get('answer') or ""
            print("Answer:", answer[:100] + "...")
            confidence = data.get('confidence')
            print(f"Confidence: {confidence}")
            if confidence:
                print("✓ Adaptive RAG Passed")
            # else: fail mostly?
            return True
        else:
            print(f"❌ Failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

def test_summarize(filename=None):
    print_section(f"Summarize (File: {filename or 'All'})")
    try:
        payload = {"length": "short"}
        if filename:
            payload["filename"] = filename
        else:
            payload["summarize_all"] = True

        response = requests.post(f"{BASE_URL}/api/summarize", json=payload, timeout=120)
        if response.status_code == 200:
            data = response.json()
            if filename:
                summary = data.get('summary') or ""
                print(f"Summary: {summary[:100]}...")
            else:
                print(f"Summaries: {len(data.get('summaries', {}) or {})}")
            print("✓ Summarize Passed")
            return True
        else:
            print(f"❌ Failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

def run_suite():
    print(f"Targeting: {BASE_URL}")
    
    if not test_health():
        print("❌ Server not available at localhost:8000. Start it with 'python api.py'")
        return

    # Use existing PDF
    pdf_path = TEST_PDF_NAME

    # Upload & Index (Wait for it)
    if not test_upload(pdf_path):
        print("Skipping further tests due to upload failure.")
        return

    # Run Feature Tests
    test_search("machine learning")
    test_chat("What is machine learning according to this book?")
    test_adaptive_rag("Summarize the key types of learning discussed.")
    test_summarize(TEST_PDF_NAME)

if __name__ == "__main__":
    run_suite()
