from search_engine import SemanticSearchEngine
import traceback

try:
    print("Initializing SemanticSearchEngine...")
    engine = SemanticSearchEngine()
    print("Searching...")
    results = engine.search("test")
    print(f"Results: {len(results)}")
except Exception:
    traceback.print_exc()
