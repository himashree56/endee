
import sys
import os
from pathlib import Path
import time
import json

# Add current dir to path
sys.path.append(os.getcwd())

from config import Config
from memory_manager import MemoryManager
from ingestion_status import IngestionStatus

def test_memory():
    print("\n--- Testing MemoryManager ---")
    print(f"Computed DATA_DIR: {Config.DATA_DIR}")
    
    # 1. Initialize
    mm = MemoryManager()
    print(f"Memory File: {mm.memory_file}")
    
    # 2. Add Interaction
    print("Adding test interaction...")
    mm.add_interaction("Test Q", "Test A", ["debug"], ["source1"])
    
    # 3. Verify File Exists
    if mm.memory_file.exists():
        print("✅ Memory file successfully created.")
        with open(mm.memory_file, 'r') as f:
            data = json.load(f)
            print(f"File content interactions: {len(data.get('interactions', []))}")
    else:
        print("❌ Memory file NOT found!")

def test_ingestion_status():
    print("\n--- Testing IngestionStatus ---")
    
    # 1. Get Instance
    tracker1 = IngestionStatus.get_instance()
    print(f"Tracker 1 ID: {id(tracker1)}")
    
    # 2. Update Status
    tracker1.update_status("test.pdf", "processing", progress=10, total=100)
    
    # 3. Get Instance Again (Simulate another module)
    tracker2 = IngestionStatus.get_instance()
    print(f"Tracker 2 ID: {id(tracker2)}")
    
    if id(tracker1) == id(tracker2):
        print("✅ Singleton works (IDs match).")
    else:
        print("❌ Singleton FAILED (IDs mismatch)!")
        
    status = tracker2.get_status("test.pdf")
    print(f"Retrieved Status: {status}")
    
    if status and status['progress'] == 10:
         print("✅ Status data persisted across instances.")
    else:
         print("❌ Status data lost!")

if __name__ == "__main__":
    test_memory()
    test_ingestion_status()
