
from search_engine import SemanticSearchEngine
import sys

def reset():
    print("WARNING: This will delete the entire vector index and local document store.")
    confirm = input("Are you sure? (y/n): ")
    if confirm.lower() != 'y':
        print("Cancelled.")
        return

    print("Resetting index...")
    engine = SemanticSearchEngine.get_instance()
    if engine.reset_index():
        print("SUCCESS: Index reset complete. Please re-upload your documents.")
    else:
        print("FAILURE: Could not reset index.")
        sys.exit(1)

if __name__ == "__main__":
    reset()
