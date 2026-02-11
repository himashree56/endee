
from endee_client import EndeeClient
import json

def debug_info():
    client = EndeeClient()
    print(f"Checking info for index: {client.index_name}")
    
    info = client.get_collection_info()
    if info:
        print("Index Found:")
        print(json.dumps(info, indent=2))
        
        # Check dimension
        dim = info.get("dim")
        print(f"Server Dimension: {dim}")
        
        from config import Config
        print(f"Config Dimension: {Config.EMBEDDING_DIM}")
        
        if dim != Config.EMBEDDING_DIM:
            print("MISMATCH: Server dimension does not match config!")
    else:
        print("Index NOT found or error retrieving info.")

if __name__ == "__main__":
    debug_info()
