from search_engine import SemanticSearchEngine
from config import Config

print(f"Config URL: {Config.ENDEE_URL}")
print(f"Config Type: {Config.VECTOR_DB_TYPE}")

try:
    engine = SemanticSearchEngine.get_instance()
    # Force initialization of client
    # engine.initialize() calls create_collection which hits DB
    success = engine.endee_client.get_collection_info()
    
    if success:
        print("SUCCESS: Engine connected to DB")
    else:
        print("FAILURE: Engine could not connect")
        # Try to initialize?
        # engine.initialize()
except Exception as e:
    print(f"FAILURE: Exception: {e}")
