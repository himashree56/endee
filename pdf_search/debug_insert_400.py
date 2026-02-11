
from endee_client import EndeeClient
import numpy as np

def debug_insert():
    client = EndeeClient()
    
    # Create a dummy vector (dimension 384)
    dim = 384
    vector = np.random.rand(dim).astype(np.float32)
    
    # Create metadata similar to ingestion
    metadata = {
        "text": "This is a test chunk.",
        "file_name": "test_doc.pdf",
        "page": 1,
        "chunk_id": 0,
        "file_path": "/app/pdfs/test_doc.pdf",
        "id": "test_doc.pdf_0"
    }
    
    import json
    
    # Variation 1: Metadata as JSON string
    print("\n--- Variation 1: Metadata as JSON string ---")
    metadata_str = metadata.copy()
    # We can't easily change the client method locally without modifying the file.
    # So we will interpret the client failure.
    
    # Actually, let's manually call the requests.post to test variations without changing client code yet.
    import requests
    from config import Config
    
    base_url = Config.ENDEE_URL
    index_name = Config.COLLECTION_NAME
    
    payload_1 = [{
        "id": "test_var_1",
        "vector": vector.tolist(),
        "metadata": json.dumps(metadata) # JSON String
    }]
    
    print("Sending Variation 1 (Metadata=String)...")
    res = requests.post(f"{base_url}/api/v1/index/{index_name}/vector/insert", json=payload_1)
    print(f"Status: {res.status_code}, Response: {res.text}")

    # Variation 2: Metadata as Empty Dict
    payload_2 = [{
        "id": "test_var_2",
        "vector": vector.tolist(),
        "metadata": {}
    }]
    print("\nSending Variation 2 (Metadata={})...")
    res = requests.post(f"{base_url}/api/v1/index/{index_name}/vector/insert", json=payload_2)
    print(f"Status: {res.status_code}, Response: {res.text}")
    
    # Variation 3: Original (Dict) but no special chars
    payload_3 = [{
        "id": "test_var_3",
        "vector": vector.tolist(),
        "metadata": {"simple": "value"}
    }]
    print("\nSending Variation 3 (Metadata={simple: value})...")
    res = requests.post(f"{base_url}/api/v1/index/{index_name}/vector/insert", json=payload_3)
    print(f"Status: {res.status_code}, Response: {res.text}")

if __name__ == "__main__":
    debug_insert()
