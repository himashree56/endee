
from endee_client import EndeeClient
from embedder import Embedder
import msgpack
import requests
import json

def debug_search():
    client = EndeeClient()
    embedder = Embedder()
    
    query = "machine learning"
    vector = embedder.embed_text(query)
    
    print(f"Searching for '{query}'...")
    
    # Manually call the API to see raw response
    data = {
        "vector": vector.tolist(),
        "k": 2,
        "include_metadata": True,
        "return_metadata": True
    }
    
    response = requests.post(
        f"{client.base_url}/api/v1/index/{client.index_name}/search",
        json=data,
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return
        
    print(f"Raw response length: {len(response.content)}")
    
    try:
        response_data = msgpack.unpackb(response.content, raw=False)
        print("\n--- Unpacked Data Structure ---")
        print(f"Type: {type(response_data)}")
        if isinstance(response_data, list):
            print(f"Total Hits: {len(response_data)}")
            for i, hit in enumerate(response_data):
                print(f"\nHit {i}: Type {type(hit)}")
                if isinstance(hit, (list, tuple)):
                    print(f"  Length: {len(hit)}")
                    for j, elem in enumerate(hit):
                        print(f"  [{j}] {type(elem)}: {str(elem)[:100]}")
                    
                    # Check metadata at index 2
                    if len(hit) > 2:
                        meta_raw = hit[2]
                        if isinstance(meta_raw, bytes):
                            print("  Metadata is bytes. Attempting unpack...")
                            try:
                                if meta_raw:
                                    meta = msgpack.unpackb(meta_raw, raw=False)
                                    print(f"  Unpacked Metadata: {meta}")
                                else:
                                    print("  Metadata bytes are empty.")
                            except Exception as e:
                                print(f"  Metadata unpack failed: {e}")
                        elif isinstance(meta_raw, dict):
                            print(f"  Metadata is dict: {meta_raw}")
        else:
            print(f"Response Data (Not List): {response_data}")
                         
    except Exception as e:
        print(f"Unpack error: {e}")

if __name__ == "__main__":
    debug_search()
