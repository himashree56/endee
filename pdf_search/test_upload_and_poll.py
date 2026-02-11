
import requests
import time
import os

BASE_URL = "http://localhost:8000"
PDF_FILE = "pdfs/test_doc.pdf"

def main():
    # 1. Create a dummy PDF if strictly needed, or use existing
    if not os.path.exists(PDF_FILE):
        print(f"File {PDF_FILE} not found. using first available pdf in directory or failing")
        # List pdfs
        import glob
        pdfs = glob.glob("pdfs/*.pdf")
        if not pdfs:
            print("No PDFs found to upload.")
            return
        upload_file = pdfs[0]
    else:
        upload_file = PDF_FILE

    print(f"Uploading {upload_file}...")
    
    with open(upload_file, 'rb') as f:
        files = {'files': (os.path.basename(upload_file), f, 'application/pdf')}
        res = requests.post(f"{BASE_URL}/api/upload", files=files)
    
    if res.status_code != 200:
        print(f"Upload failed: {res.text}")
        return
        
    print("Upload initiated. Response:", res.json())
    filenames = res.json().get("filenames", [])
    
    # 2. Poll Status
    print("Polling status...")
    for _ in range(10): # Poll for 10 seconds
        res = requests.get(f"{BASE_URL}/api/ingestion/status")
        data = res.json()
        print("Status:", data)
        
        # Check if completed
        all_completed = True
        status_map = data.get("status", {})
        for name in filenames:
            s = status_map.get(name)
            if s:
                print(f"  {name}: {s.get('status')} - {s.get('progress')}/{s.get('total')}")
                if s.get('status') != 'completed' and s.get('status') != 'failed':
                    all_completed = False
            else:
                print(f"  {name}: Not found in status yet")
                all_completed = False
                
        if all_completed and len(filenames) > 0:
            print("Ingestion Completed!")
            break
            
        time.sleep(1)

if __name__ == "__main__":
    main()
