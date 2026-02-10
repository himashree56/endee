import os
from config import Config
import requests
from embedder import Embedder

# Force config load
print(f"Testing Full Chain...")
print(f"DB URL: {Config.ENDEE_URL}")
print(f"API Key Present: {bool(Config.OPENROUTER_API_KEY)}")

def test_chain():
    # 1. Test DB Connection
    print("\n[1] Testing DB Connection...")
    try:
        resp = requests.get(f"{Config.ENDEE_URL}/api/v1/index/list", timeout=30)
        if resp.status_code == 200:
            print("✓ DB Connected")
        else:
            print(f"✗ DB Failed: {resp.status_code}")
            return False
    except Exception as e:
        print(f"✗ DB Exception: {e}")
        return False

    # 2. Test Embedding (FastEmbed)
    print("\n[2] Testing Embedding...")
    try:
        embedder = Embedder()
        vector = embedder.embed_text("Test query")
        print(f"✓ Embedded text (dim={len(vector)})")
    except Exception as e:
        print(f"✗ Embedding Failed: {e}")
        return False

    # 3. Test Search (DB + Embedding)
    print("\n[3] Testing Vector Search...")
    from endee_client import EndeeClient
    client = EndeeClient()
    try:
        results = client.search(vector, top_k=1)
        print(f"✓ Search completed. Found {len(results)} results.")
    except Exception as e:
        print(f"✗ Search Failed: {e}")
        return False

    # 4. Test LLM (OpenRouter)
    print("\n[4] Testing LLM (OpenRouter)...")
    from langchain_openai import ChatOpenAI
    try:
        llm = ChatOpenAI(
            model=Config.LLM_MODEL,
            api_key=Config.OPENROUTER_API_KEY,
            base_url=Config.OPENROUTER_BASE_URL
        )
        msg = llm.invoke("Hello, are you working?")
        print(f"✓ LLM Response: {msg.content}")
    except Exception as e:
        print(f"✗ LLM Failed: {e}")
        return False
        
    print("\n[SUCCESS] Full Chain Verified!")
    return True

if __name__ == "__main__":
    test_chain()
